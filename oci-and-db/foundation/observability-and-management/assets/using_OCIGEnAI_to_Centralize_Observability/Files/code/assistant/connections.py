"""Administrator-managed MCP registrations. Credentials stay outside model context."""
import configparser
import copy
import hashlib
import json
import os
import re
import secrets
import sqlite3
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Literal

import oci
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey
from pydantic import BaseModel,ConfigDict,Field,SecretStr,field_validator
from .policy import PolicyError
from .remote_transport import validate_remote_url


class ConnectionError(ValueError):pass


def ocid(value,kind):
    if not re.fullmatch(r'ocid1\.'+kind+r'\.[A-Za-z0-9._-]{8,240}',value or ''):
        raise ConnectionError('Provide a valid '+kind+' OCID')
    return value


def admin_allowed(policy,user):
    grants=policy.get('administrators',{})
    return user['sub'] in grants.get('subjects',[]) or bool(set(user.get('groups',[]))&set(grants.get('groups',[])))


def environment_binding(env):
    if not env.get('connection_refs'):return ''
    data={key:env.get(key) for key in ('compartment_id','tenancy_id','region','connection_refs','connection_revisions')}
    return hashlib.sha256(json.dumps(data,sort_keys=True).encode()).hexdigest()


def environment_sources(env):
    refs=env.get('connection_refs')
    return {k for k,v in refs.items() if v} if refs is not None else {'db','logan'}


class ConnectionInput(BaseModel):
    model_config=ConfigDict(extra='forbid')
    label:str=Field(min_length=1,max_length=80)
    kind:Literal['db','logan']
    transport:Literal['managed','https']='managed'
    auth_mode:Literal['existing_profile','api_key']='existing_profile'
    profile:str=Field(default='DEFAULT',max_length=64)
    region:str=Field(default='',max_length=64)
    tenancy_id:str=Field(default='',max_length=256)
    user_id:str=Field(default='',max_length=256)
    fingerprint:str=Field(default='',max_length=64)
    private_key:SecretStr=Field(default=SecretStr(''),max_length=65536)
    key_passphrase:SecretStr=Field(default=SecretStr(''),max_length=1024)
    namespace:str=Field(default='',max_length=128)
    url:str=Field(default='',max_length=2048)
    bearer_token:SecretStr=Field(default=SecretStr(''),max_length=8192)
    test_compartment_id:str=Field(max_length=256)

    @field_validator('label','namespace','region','profile','fingerprint','tenancy_id','user_id','test_compartment_id','url')
    @classmethod
    def clean(cls,value):
        if any(ord(c)<32 for c in value):raise ValueError('Control characters are not allowed')
        return value.strip()


class EnvironmentInput(BaseModel):
    model_config=ConfigDict(extra='forbid')
    label:str=Field(min_length=1,max_length=80)
    compartment_id:str=Field(max_length=256)
    db_connection_id:str=Field(default='',max_length=64)
    logan_connection_id:str=Field(default='',max_length=64)
    subjects:list[str]=Field(default_factory=list,max_length=100)
    groups:list[str]=Field(default_factory=list,max_length=100)


def _secure_write(path,text):
    descriptor=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    with os.fdopen(descriptor,'w') as stream:stream.write(text)


class ConnectionRegistry:
    def __init__(self,settings):
        self.settings=settings;self.path=settings.data_dir/'mcp-connections.sqlite3'
        settings.data_dir.mkdir(parents=True,exist_ok=True)
        key=os.getenv('CONNECTION_ENCRYPTION_KEY','')
        try:self.cipher=Fernet(key.encode()) if key else None
        except (ValueError,TypeError):self.cipher=None
        with self.db() as c:
            c.executescript('''
              CREATE TABLE IF NOT EXISTS connections (id TEXT PRIMARY KEY, public TEXT NOT NULL, encrypted TEXT NOT NULL);
              CREATE TABLE IF NOT EXISTS environments (id TEXT PRIMARY KEY, data TEXT NOT NULL);
              CREATE TABLE IF NOT EXISTS config_audit (created REAL, actor TEXT, action TEXT, object_id TEXT);
            ''')
        self.path.chmod(0o600)

    @contextmanager
    def db(self):
        c=sqlite3.connect(self.path,timeout=15);c.row_factory=sqlite3.Row
        try:
            with c:yield c
        finally:c.close()

    def require_key(self):
        if self.cipher is None:raise ConnectionError('The administrator must configure CONNECTION_ENCRYPTION_KEY before adding MCP connections.')

    def audit(self,c,actor,action,object_id):
        c.execute('INSERT INTO config_audit VALUES (?,?,?,?)',(time.time(),actor,action,object_id))

    def list_connections(self):
        with self.db() as c:return [json.loads(r[0]) for r in c.execute('SELECT public FROM connections ORDER BY rowid DESC')]

    def get(self,identifier,private=False):
        with self.db() as c:r=c.execute('SELECT * FROM connections WHERE id=?',(identifier,)).fetchone()
        if not r:raise ConnectionError('MCP connection not found')
        public=json.loads(r['public'])
        if not private:return public
        self.require_key()
        try:payload=json.loads(self.cipher.decrypt(r['encrypted'].encode()))
        except Exception:raise ConnectionError('Stored MCP credentials could not be opened with the configured encryption key.') from None
        return public,payload

    def profile_names(self):
        parser=configparser.ConfigParser(interpolation=None)
        parser.read(os.getenv('OCI_CONFIG_FILE','/secrets/oci/config'))
        return ['DEFAULT',*parser.sections()] if parser.defaults() else parser.sections()

    def prepare_input(self,body):
        ocid(body.test_compartment_id,'compartment')
        if not body.label.strip():raise ConnectionError('Provide a connection name')
        if body.kind=='logan' and not re.fullmatch(r'[A-Za-z0-9_-]{1,128}',body.namespace):raise ConnectionError('Provide the Log Analytics namespace')
        if body.transport=='https':
            try:validate_remote_url(body.url)
            except ValueError as exc:raise ConnectionError(str(exc)) from None
        if body.auth_mode=='existing_profile':
            if not re.fullmatch(r'[A-Za-z0-9_.-]{1,64}',body.profile):raise ConnectionError('Provide an operator-configured profile name')
            try:cfg=oci.config.from_file(os.getenv('OCI_CONFIG_FILE','/secrets/oci/config'),body.profile)
            except Exception:raise ConnectionError('The selected OCI profile is not available to this deployment.') from None
            tenant=cfg.get('tenancy','');region=body.region or cfg.get('region','')
        else:
            tenant=ocid(body.tenancy_id,'tenancy');ocid(body.user_id,'user');region=body.region
            password=body.key_passphrase.get_secret_value()
            if any(c in password for c in '\r\n\0'):raise ConnectionError('The key passphrase must be a single line')
            try:
                key=serialization.load_pem_private_key(body.private_key.get_secret_value().encode(),password=password.encode() if password else None)
                if not isinstance(key,RSAPrivateKey) or key.key_size<2048:raise ValueError()
            except Exception:raise ConnectionError('Provide a valid RSA private key of at least 2048 bits and its passphrase if encrypted.') from None
            der=key.public_key().public_bytes(serialization.Encoding.DER,serialization.PublicFormat.SubjectPublicKeyInfo)
            digest=hashlib.md5(der,usedforsecurity=False).hexdigest();actual=':'.join(digest[i:i+2] for i in range(0,len(digest),2))
            if body.fingerprint and body.fingerprint.lower()!=actual:raise ConnectionError('The fingerprint does not match the private key')
        ocid(tenant,'tenancy')
        if not re.fullmatch(r'[a-z]{2,8}-[a-z0-9-]{2,45}-[1-9][0-9]?',region):raise ConnectionError('Provide an OCI region such as eu-frankfurt-1')
        token=body.bearer_token.get_secret_value()
        if any(c in token for c in '\r\n\0'):raise ConnectionError('The bearer token must be a single line')
        payload={k:getattr(body,k) for k in ('auth_mode','profile','user_id','url','namespace')}
        payload.update(region=region,tenancy_id=tenant,fingerprint=actual if body.auth_mode=='api_key' else '',
            private_key=body.private_key.get_secret_value() if body.auth_mode=='api_key' else '',
            key_passphrase=body.key_passphrase.get_secret_value() if body.auth_mode=='api_key' else '',bearer_token=token)
        return payload

    def create(self,body,actor):
        self.require_key();payload=self.prepare_input(body);identifier=secrets.token_hex(12)
        public={'id':identifier,'label':body.label.strip(),'kind':body.kind,'transport':body.transport,'auth_mode':body.auth_mode,
            'profile':body.profile if body.auth_mode=='existing_profile' else '', 'region':payload['region'],'tenancy_id':payload['tenancy_id'],
            'namespace':body.namespace,'url':body.url if body.transport=='https' else '',
            'test_compartment_id':body.test_compartment_id,'status':'pending','enabled':True,'created_by':actor,'created':time.time(),'revision':1}
        encrypted=self.cipher.encrypt(json.dumps(payload).encode()).decode()
        with self.db() as c:
            c.execute('INSERT INTO connections VALUES (?,?,?)',(identifier,json.dumps(public),encrypted));self.audit(c,actor,'connection_created',identifier)
        return public

    def mark_testing(self,identifier,actor):
        public=self.get(identifier);public.update(status='pending',last_error='')
        with self.db() as c:
            c.execute('UPDATE connections SET public=? WHERE id=?',(json.dumps(public),identifier))
            self.audit(c,actor,'connection_test_started',identifier)

    def test_result(self,identifier,actor,ok,error=''):
        public=self.get(identifier);public.update(status='ready' if ok else 'failed',last_test_at=time.time(),last_error=error[:200])
        with self.db() as c:
            c.execute('UPDATE connections SET public=? WHERE id=?',(json.dumps(public),identifier));self.audit(c,actor,'connection_test_passed' if ok else 'connection_test_failed',identifier)
        return public

    def set_enabled(self,identifier,enabled,actor):
        public=self.get(identifier);public['enabled']=bool(enabled);public['revision']+=1
        with self.db() as c:
            c.execute('UPDATE connections SET public=? WHERE id=?',(json.dumps(public),identifier));self.audit(c,actor,'connection_enabled' if enabled else 'connection_disabled',identifier)
        return public

    def list_environments(self):
        with self.db() as c:return [json.loads(r[0]) for r in c.execute('SELECT data FROM environments ORDER BY rowid DESC')]

    def environment_connections(self,body):
        selected={}
        for kind,key in [('db',body.db_connection_id),('logan',body.logan_connection_id)]:
            if not key:continue
            item=self.get(key)
            if item['kind']!=kind or item['status']!='ready' or not item['enabled']:raise ConnectionError('Choose a tested, enabled connection of the correct type')
            selected[kind]=item
        if not selected:raise ConnectionError('Assign at least one MCP connection')
        scopes={(item['tenancy_id'],item['region']) for item in selected.values()}
        if len(scopes)!=1:raise ConnectionError('Connections assigned to one environment must use the same tenancy and region')
        return selected

    def save_environment(self,body,actor,verified_name,identifier=None):
        if identifier is not None and not any(e['id']==identifier for e in self.list_environments()):
            raise ConnectionError('Additional environment not found; deployment environments cannot be overwritten here')
        ocid(body.compartment_id,'compartment');selected=self.environment_connections(body)
        identifier=identifier or 'mcp-'+secrets.token_hex(10)
        if not body.label.strip() or any(ord(c)<32 for c in body.label):raise ConnectionError('Provide an environment label without control characters')
        for value in body.subjects+body.groups:
            if not value.strip() or len(value)>200 or any(ord(c)<32 for c in value):raise ConnectionError('Provide valid sign-in subjects or group names')
        if not body.subjects and not body.groups:raise ConnectionError('Assign at least one sign-in subject or group')
        first=next(iter(selected.values()))
        data={'id':identifier,'label':body.label.strip(),'compartment_id':body.compartment_id,'compartment_name':verified_name,
            'subjects':list(dict.fromkeys(body.subjects)),'groups':list(dict.fromkeys(body.groups)),
            'tenancy_id':first['tenancy_id'],'region':first['region'],'enabled':True,
            'connection_refs':{k:v['id'] for k,v in selected.items()},'connection_revisions':{k:v['revision'] for k,v in selected.items()}}
        with self.db() as c:
            c.execute('INSERT OR REPLACE INTO environments VALUES (?,?)',(identifier,json.dumps(data)));self.audit(c,actor,'environment_assigned',identifier)
        return data

    def disable_environment(self,identifier,actor):
        with self.db() as c:
            row=c.execute('SELECT data FROM environments WHERE id=?',(identifier,)).fetchone()
            if not row:raise ConnectionError('Environment not found')
            data=json.loads(row[0]);data['enabled']=False;c.execute('UPDATE environments SET data=? WHERE id=?',(json.dumps(data),identifier));self.audit(c,actor,'environment_disabled',identifier)

    def merged_policy(self,base):
        result=copy.deepcopy(base)
        for env in self.list_environments():
            if not env['enabled']:continue
            try:
                refs=env['connection_refs'];items={k:self.get(v) for k,v in refs.items()}
                if not items or any(not v['enabled'] or v['status']!='ready' for v in items.values()):continue
                if any(v['tenancy_id']!=env['tenancy_id'] or v['region']!=env['region'] for v in items.values()):continue
                current={**env,'connection_revisions':{k:v['revision'] for k,v in items.items()}}
                result['environments'][env['id']]=current
            except ConnectionError:continue
        return result

    def _oci_material(self,public,payload,directory,compartment):
        if payload['auth_mode']=='existing_profile':
            try:cfg=oci.config.from_file(os.getenv('OCI_CONFIG_FILE','/secrets/oci/config'),payload['profile'])
            except Exception:raise ConnectionError('The selected OCI profile is no longer available.') from None
            if cfg.get('tenancy')!=public['tenancy_id']:raise ConnectionError('The OCI profile tenancy changed. Register and test a new connection.')
            user=cfg['user'];fingerprint=cfg['fingerprint'];key_file=cfg.get('key_file');key_content=cfg.get('key_content');password=cfg.get('pass_phrase','') or ''
            if key_content:
                key_file=str(directory/'key.pem');_secure_write(Path(key_file),key_content)
            if not key_file:raise ConnectionError('The profile has no signing key')
        else:
            user=payload['user_id'];fingerprint=payload['fingerprint'];key_file=str(directory/'key.pem');password=payload['key_passphrase'];_secure_write(Path(key_file),payload['private_key'])
        config={'user':user,'fingerprint':fingerprint,'tenancy':public['tenancy_id'],'region':public['region'],'key_file':key_file}
        if password:config['pass_phrase']=password
        # Reject config-file interpolation/injection, including operator profile errors.
        if any(any(c in str(v) for c in '\r\n\0') for v in config.values()):raise ConnectionError('OCI profile fields must be single-line values')
        parser=configparser.ConfigParser(interpolation=None);parser['DEFAULT']=config
        path=directory/'config'
        with path.open('x') as f:parser.write(f)
        path.chmod(0o600)
        access={'environments':{'target':{'compartment_id':compartment}}}
        _secure_write(directory/'access.json',json.dumps(access))
        return {'OCI_AUTH_TYPE':'api_key','OCI_MCP_AUTH_TYPE':'api_key','OCI_CONFIG_FILE':str(path),'OCI_CONFIG_PATH':str(path),
            'OCI_CONFIG_PROFILE':'DEFAULT','OCI_REGION':public['region'],'CONFIG_DIR':str(directory)}

    @contextmanager
    def runtime_config(self,base,env,home,connection_ids=None,require_ready=True):
        """Materialize credentials only while clients are alive; no subprocess commands from users."""
        refs=connection_ids if connection_ids is not None else env.get('connection_refs')
        if refs is None:
            yield copy.deepcopy(base);return
        self.require_key();home.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='credentials-',dir=home) as folder:
            folder=Path(folder);folder.chmod(0o700);config={k:copy.deepcopy(v) for k,v in base.items() if k not in {'db','logan','identity'}}
            identity=None
            for kind,identifier in refs.items():
                public,payload=self.get(identifier,private=True)
                if public['kind']!=kind or not public['enabled'] or (require_ready and public['status']!='ready'):raise ConnectionError('The environment MCP connection is not ready')
                if env.get('tenancy_id') and public['tenancy_id']!=env['tenancy_id']:raise ConnectionError('MCP tenancy does not match the environment')
                if env.get('region') and public['region']!=env['region']:raise ConnectionError('MCP region does not match the environment')
                directory=folder/identifier;directory.mkdir(mode=0o700)
                variables=self._oci_material(public,payload,directory,env['compartment_id'])
                identity=identity or {'command':base['identity']['command'],'args':['-m','assistant.identity_mcp'],'env':variables,'isolate_oci_env':True,'connection_id':identifier}
                if public['transport']=='managed':
                    if kind=='db':spec={'command':base['db']['command'],'args':[],'env':variables}
                    else:
                        variables={**variables,'OCI_LA_AUTH_TYPE':'config_file','OCI_LA_NAMESPACE':payload['namespace'],'OCI_LA_COMPARTMENT':env['compartment_id'],'OCI_LOGAN_MCP_READ_ONLY':'true'}
                        spec={'command':base['logan']['command'],'args':['-m','assistant.logan_launcher','--user',identifier],'env':variables}
                    spec.update(isolate_oci_env=True,connection_id=identifier)
                else:
                    validate_remote_url(payload['url']);spec={'transport':'https','url':payload['url'],'bearer_token':payload['bearer_token'],'public_only':True,'connection_id':identifier}
                config[kind]=spec
            if identity is None:raise ConnectionError('No MCP connection is assigned to this environment')
            config['identity']=identity
            yield config
