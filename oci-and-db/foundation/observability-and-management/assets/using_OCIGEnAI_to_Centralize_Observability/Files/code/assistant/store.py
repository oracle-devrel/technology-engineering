import hashlib
import json
import secrets
import sqlite3
import time
from contextlib import contextmanager
from datetime import datetime, timezone


class ConversationScopeError(ValueError):
    pass


class Store:
    def __init__(self, path):
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        with self.db() as c:
            c.executescript('''
            PRAGMA journal_mode=WAL;
            CREATE TABLE IF NOT EXISTS sessions (id TEXT PRIMARY KEY, user TEXT, csrf TEXT, expires REAL);
            CREATE TABLE IF NOT EXISTS runs (id TEXT PRIMARY KEY, owner TEXT, environment TEXT,
              question TEXT, status TEXT, answer TEXT, events TEXT, created REAL);
            ''')
            if 'model' not in {r['name'] for r in c.execute('PRAGMA table_info(runs)')}:
                c.execute("ALTER TABLE runs ADD COLUMN model TEXT NOT NULL DEFAULT '{}'")
            c.execute('''CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY, owner TEXT NOT NULL, environment TEXT NOT NULL,
                compartment_id TEXT NOT NULL, title TEXT NOT NULL, created REAL NOT NULL,
                trace_id TEXT NOT NULL, root_span_id TEXT NOT NULL, root_emitted INTEGER NOT NULL DEFAULT 0)''')
            columns={r['name'] for r in c.execute('PRAGMA table_info(runs)')}
            for name,definition in [('conversation_id','TEXT'),('turn_index','INTEGER NOT NULL DEFAULT 1'),
                    ('utc_start',"TEXT NOT NULL DEFAULT ''"),('utc_end',"TEXT NOT NULL DEFAULT ''"),
                    ('interaction_span_id',"TEXT NOT NULL DEFAULT ''")]:
                if name not in columns:c.execute(f'ALTER TABLE runs ADD COLUMN {name} {definition}')
            if 'routing' not in columns:c.execute("ALTER TABLE runs ADD COLUMN routing TEXT NOT NULL DEFAULT '{}'")
            c.execute('CREATE INDEX IF NOT EXISTS runs_conversation ON runs(conversation_id,turn_index)')
            if 'connection_binding' not in {r['name'] for r in c.execute('PRAGMA table_info(conversations)')}:
                c.execute("ALTER TABLE conversations ADD COLUMN connection_binding TEXT NOT NULL DEFAULT ''")
            c.execute("UPDATE runs SET status='interrupted', answer='The assistant restarted. Please submit the question again.' WHERE status IN ('queued','running')")

    @contextmanager
    def db(self):
        c = sqlite3.connect(self.path, timeout=15)
        c.row_factory = sqlite3.Row
        try:
            with c:
                yield c
        finally:
            c.close()

    @staticmethod
    def digest(value):
        return hashlib.sha256(value.encode()).hexdigest()

    def session(self, user):
        token, csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
        with self.db() as c:
            c.execute("DELETE FROM sessions WHERE expires < ?", (time.time(),))
            c.execute("INSERT INTO sessions VALUES (?,?,?,?)", (self.digest(token), json.dumps(user), csrf, time.time()+28800))
        return token

    def user(self, token):
        with self.db() as c:
            r = c.execute("SELECT * FROM sessions WHERE id=? AND expires>?", (self.digest(token), time.time())).fetchone()
        return (json.loads(r['user']), r['csrf']) if r else None

    def logout(self, token):
        with self.db() as c:
            c.execute("DELETE FROM sessions WHERE id=?", (self.digest(token),))

    def create_run(self, owner, environment, question, daily_limit, model=None, conversation_id=None, compartment_id='', window=None,routing=None,connection_binding=''):
        day_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0).timestamp()
        with self.db() as c:
            c.execute("BEGIN IMMEDIATE")
            n = c.execute("SELECT count(*) FROM runs WHERE owner=? AND created>=?", (owner, day_start)).fetchone()[0]
            active = c.execute("SELECT count(*) FROM runs WHERE owner=? AND status IN ('queued','running')", (owner,)).fetchone()[0]
            if n >= daily_limit or active:
                raise ValueError("Your daily limit has been reached or an investigation is already running")
            if conversation_id:
                conversation=c.execute('SELECT * FROM conversations WHERE id=? AND owner=?',(conversation_id,owner)).fetchone()
                if not conversation:raise LookupError('Conversation not found')
                if conversation['environment']!=environment or conversation['compartment_id']!=compartment_id:
                    raise ConversationScopeError('Start a new conversation to change environments.')
                if conversation['connection_binding']!=connection_binding:
                    raise ConversationScopeError('The environment MCP connections changed. Start a new conversation.')
            else:
                conversation_id=secrets.token_hex(16)
                c.execute('INSERT INTO conversations (id,owner,environment,compartment_id,title,created,trace_id,root_span_id) VALUES (?,?,?,?,?,?,?,?)',
                    (conversation_id,owner,environment,compartment_id,question[:90],time.time(),secrets.token_hex(16),secrets.token_hex(8)))
                c.execute('UPDATE conversations SET connection_binding=? WHERE id=?',(connection_binding,conversation_id))
            turn=c.execute('SELECT coalesce(max(turn_index),0)+1 FROM runs WHERE conversation_id=?',(conversation_id,)).fetchone()[0]
            rid = secrets.token_hex(16)
            public_model = {k:model[k] for k in ('id','label','region')} if model else {}
            c.execute("INSERT INTO runs (id,owner,environment,question,status,answer,events,created,model,conversation_id,turn_index,utc_start,utc_end) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)", (rid, owner, environment, question, 'queued', '', '[]', time.time(),json.dumps(public_model),conversation_id,turn,*(window or ('',''))))
            c.execute('UPDATE runs SET routing=? WHERE id=?',(json.dumps(routing or {}),rid))
        return rid

    def update(self, rid, status=None, answer=None, events=None, interaction_span_id=None):
        with self.db() as c:
            for column, value in [('status',status),('answer',answer),('events',json.dumps(events) if events is not None else None),('interaction_span_id',interaction_span_id)]:
                if value is not None:
                    c.execute(f"UPDATE runs SET {column}=? WHERE id=?", (value,rid))

    def get(self, rid, owner):
        with self.db() as c:
            r = c.execute("SELECT runs.*,conversations.trace_id,conversations.root_span_id,conversations.root_emitted,conversations.compartment_id AS conversation_compartment,conversations.created AS conversation_created FROM runs LEFT JOIN conversations ON conversations.id=runs.conversation_id WHERE runs.id=? AND runs.owner=?", (rid,owner)).fetchone()
        if not r:
            return None
        result = dict(r)
        result['events'] = json.loads(result['events'])
        result['model'] = json.loads(result['model'])
        result['routing'] = json.loads(result['routing'])
        return result

    def history(self, owner):
        with self.db() as c:
            rows = [dict(r) for r in c.execute("SELECT id, environment, question, status, created, model, conversation_id FROM runs WHERE owner=? ORDER BY created DESC LIMIT 20", (owner,))]
        for row in rows:
            row['model'] = json.loads(row['model'])
        return rows

    def conversations(self, owner):
        with self.db() as c:
            return [dict(r) for r in c.execute('''SELECT conversations.*,count(runs.id) AS turn_count,max(runs.created) AS updated
                FROM conversations LEFT JOIN runs ON runs.conversation_id=conversations.id
                WHERE conversations.owner=? GROUP BY conversations.id ORDER BY updated DESC LIMIT 50''',(owner,))]

    def conversation(self, cid, owner):
        with self.db() as c:
            row=c.execute('SELECT * FROM conversations WHERE id=? AND owner=?',(cid,owner)).fetchone()
            if not row:return None
            result=dict(row)
            ids=[r[0] for r in c.execute('SELECT id FROM runs WHERE conversation_id=? AND owner=? ORDER BY turn_index DESC LIMIT 100',(cid,owner))]
            result['turn_count']=c.execute('SELECT count(*) FROM runs WHERE conversation_id=? AND owner=?',(cid,owner)).fetchone()[0]
        result['turns']=[self.get(rid,owner) for rid in reversed(ids)]
        result['has_earlier_turns']=result['turn_count']>len(ids)
        return result

    def context(self, rid, owner, max_turns=6, max_chars=24000):
        """Only earlier completed answers from this owner's exact conversation."""
        current=self.get(rid,owner)
        if not current or not current['conversation_id']:return []
        with self.db() as c:
            rows=[dict(r) for r in c.execute('''SELECT question,answer,status,utc_start,utc_end,turn_index
                FROM runs WHERE owner=? AND conversation_id=? AND turn_index<? AND answer!=''
                AND status IN ('complete','partial') ORDER BY turn_index DESC LIMIT ?''',
                (owner,current['conversation_id'],current['turn_index'],max_turns))]
        selected=[];remaining=max_chars
        for row in rows:
            size=len(row['question'])+len(row['answer'])
            if size>remaining:
                if selected:break
                row['answer']=row['answer'][:max(0,remaining-len(row['question']))]+'\n[Prior answer shortened for context]'
            selected.append(row);remaining-=min(size,remaining)
        return list(reversed(selected))

    def mark_root_emitted(self, cid):
        with self.db() as c:c.execute('UPDATE conversations SET root_emitted=1 WHERE id=?',(cid,))
