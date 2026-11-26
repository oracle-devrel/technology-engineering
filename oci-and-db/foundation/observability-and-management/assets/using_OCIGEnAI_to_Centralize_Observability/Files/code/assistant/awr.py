"""Bind AWR identifiers to a verified managed database and completed snapshot interval."""
import re
from datetime import datetime
from .policy import ToolPrerequisiteError


def walk(value):
    if isinstance(value,dict):
        yield value
        for v in value.values():yield from walk(v)
    elif isinstance(value,list):
        for v in value:yield from walk(v)


def timestamp(value):
    try:
        result=datetime.fromisoformat(str(value).replace('Z','+00:00'))
        return result if result.tzinfo else None
    except ValueError:return None


class AWRScope:
    def __init__(self,window):
        self.start,self.end=map(timestamp,window)
        self.databases={};self.snapshots={};self.effective=None

    def prepare(self,op,args):
        key=(args.get('managed_database_id'),str(args.get('awr_db_id','')))
        if op not in {'list_awr_dbs','list_awr_db_snapshots','get_awr_db_report'}:return
        for field in ('time_greater_than_or_equal_to','time_less_than_or_equal_to'):
            if field in args:
                value=timestamp(args[field])
                if value is None or not self.start<=value<=self.end:raise ToolPrerequisiteError('AWR timestamps must remain inside the selected UTC window.')
        if op!='list_awr_dbs':
            if key not in self.databases:raise ToolPrerequisiteError('Discover this AWR database using list_awr_dbs for the same managed_database_id first. Never invent or reuse an AWR ID from another database.')
            container=self.databases[key]
            if 'container_id' in args and args['container_id']!=container:raise ToolPrerequisiteError('Use the container_id returned for this AWR database.')
            if container is not None:args['container_id']=container
        # Snapshot IDs cannot override the selected time interval during discovery.
        if op!='get_awr_db_report':
            args.setdefault('limit',100)
            if any(k in args for k in ('begin_sn_id_greater_than_or_equal_to','end_sn_id_less_than_or_equal_to')):raise ToolPrerequisiteError('Discover AWR snapshots with the selected time bounds; omit snapshot-ID filters.')
            args['time_greater_than_or_equal_to']=self.start.isoformat()
            args['time_less_than_or_equal_to']=self.end.isoformat()
            return
        groups=self.snapshots.get(key,{})
        pairs=[]
        for (instance,startup),rows in groups.items():
            ordered=sorted(rows.items(),key=lambda row:row[1])
            if len(ordered)<2:continue
            begin=ordered[0][0];end=ordered[-1][0]
            if begin in rows and end in rows and begin<end and rows[begin]<rows[end]:pairs.append((rows[end]-rows[begin],instance,begin,end,rows[begin],rows[end]))
        if not pairs:raise ToolPrerequisiteError('No complete AWR snapshot pair was verified inside this selected window. Call list_awr_db_snapshots after list_awr_dbs; if fewer than two completed snapshots fit, choose a wider look-back. Do not use logs as a SQL ranking.')
        _,instance,begin,end,start,stop=max(pairs,key=lambda row:row[0])
        for field,value in [('begin_sn_id_greater_than_or_equal_to',begin),('end_sn_id_less_than_or_equal_to',end)]:
            if field in args and args[field]!=value:raise ToolPrerequisiteError('Omit snapshot-ID filters for this workflow. The gateway selects the widest verified same-startup pair inside the selected window: '+str(begin)+' to '+str(end)+'. A narrower model-chosen pair does not represent the selected interval.')
        if 'inst_nums' in args and args['inst_nums']!=[str(instance)]:raise ToolPrerequisiteError('Use the single instance verified by the selected snapshot pair.')
        if args.get('report_format','TEXT')!='TEXT' or args.get('report_type','AWR')!='AWR':raise ToolPrerequisiteError('This SQL workflow supports TEXT AWR reports only.')
        args.update(begin_sn_id_greater_than_or_equal_to=begin,end_sn_id_less_than_or_equal_to=end,inst_nums=[str(instance)],report_format='TEXT',report_type='AWR')
        # Verified snapshot IDs determine the interval. Do not send competing time selectors.
        args.pop('time_greater_than_or_equal_to',None);args.pop('time_less_than_or_equal_to',None)
        self.effective={'start':start.isoformat(),'end':stop.isoformat(),'begin_snapshot':begin,'end_snapshot':end,'instance':instance,
            'verified_snapshot_count':sum(len(rows) for rows in groups.values()),'startup_instance_groups':len(groups),
            'note':'Widest verified same-startup interval inside the selected window. Other snapshot pairs may exist. This interval does not cover the whole selected window; restart boundaries and incomplete edge intervals are excluded.'}

    def observe(self,op,args,result):
        managed=args.get('managed_database_id')
        if op=='list_awr_dbs':
            for row in walk(result):
                if row.get('awr_db_id') is not None and 'db_name' in row:
                    self.databases[(managed,str(row['awr_db_id']))]=row.get('container_id')
        if op=='list_awr_db_snapshots':
            key=(managed,str(args['awr_db_id']));groups=self.snapshots.setdefault(key,{})
            for row in walk(result):
                end=timestamp(row.get('time_end'));snap=row.get('snapshot_id');instance=row.get('instance_number')
                if str(row.get('awr_db_id'))!=key[1] or not isinstance(snap,int) or not isinstance(instance,int):continue
                if end is None or not self.start<=end<=self.end or row.get('error_count',0):continue
                if not row.get('time_db_startup'):continue
                groups.setdefault((instance,str(row['time_db_startup'])),{})[snap]=end


def sql_sections(result,effective):
    content=next((r['content'] for r in walk(result) if isinstance(r.get('content'),str)),None)
    if not content:return {'partial':True,'reason':'AWR report did not return text content.','effective_window':effective}
    # TEXT reports repeat headings on each page and append DB/instance/snapshot labels.
    heading=re.compile(r'^[ \t]*SQL ordered by ([^\n]+?)(?:[ \t]+DB/Inst:[^\n]*)?[ \t]*$',re.I|re.M)
    matches=list(heading.finditer(content));sections=[];seen=set()
    for index,match in enumerate(matches):
        kind=match.group(1).strip()
        if kind.lower() not in {'elapsed time','cpu time','executions'} or kind.lower() in seen:continue
        seen.add(kind.lower())
        stop=next((m.start() for m in matches[index+1:] if m.group(1).strip().lower()!=kind.lower()),len(content))
        text=content[match.start():stop].strip()
        end=re.search(r'\n[ \t]*(?:Instance Activity Stats|Tablespace IO Stats|Complete List of SQL Text)[^\n]*',text,re.I)
        if end:text=text[:end.start()]
        sample=text[:5500]
        if len(text)>5500:sample=sample.rsplit('\n',1)[0]
        sections.append({'section':'SQL ordered by '+kind,'text':sample,'truncated':len(text)>5500})
    return {'effective_window':effective,'sql_sections':sections,'partial':not sections or any(s['truncated'] for s in sections),
        'report_selection':{'original_characters':len(content),'included_sections':len(sections),'note':'Only selected SQL ranking sections are included. SQL text may be abbreviated in AWR. Report absence or truncation explicitly; no complete workload claim.'}}
