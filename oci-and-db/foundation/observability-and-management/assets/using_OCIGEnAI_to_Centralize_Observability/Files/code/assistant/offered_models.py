import asyncio
import hashlib
import json
import re
import secrets
import time
from datetime import datetime, timezone

from .mcp_client import MCPClients
from .models import ModelCatalog


def field(row, camel, snake=None, default=None):
    return row.get(camel,row.get(snake or camel,default))


def enum_values(values):
    out=set()
    for v in values or []:
        if isinstance(v,str): out.add(v.upper())
        elif isinstance(v,dict):
            for k in ('name','type','capability','servingMode','serving_mode'):
                if isinstance(v.get(k),str): out.add(v[k].upper())
    return out


def past(value):
    if not value: return False
    try: return datetime.fromisoformat(value.replace('Z','+00:00'))<=datetime.now(timezone.utc)
    except (ValueError,TypeError): return True


def normalize_catalog(payload, allow_proxy=False):
    """Show all returned offerings; enable only identifiable on-demand Chat adapters."""
    region=payload['region']
    inventory=payload.get('inventory',[])
    discovery=payload.get('discovery',[])
    def norm(x): return re.sub(r'[^a-z0-9]','',str(x).lower())
    rows=[]; matched=set()
    for item in inventory:
        mid=item.get('id',''); label=field(item,'displayName','display_name') or mid
        if not mid.startswith('ocid1.generativeaimodel.'): continue
        links=[(i,d) for i,d in enumerate(discovery) if norm(field(d,'modelId','model_id')) in {norm(mid),norm(label)}]
        index,d=links[0] if len(links)==1 else (None,{})
        if index is not None: matched.add(index)
        vendor=item.get('vendor') or d.get('vendor') or 'Unknown'
        caps=enum_values(item.get('capabilities') or d.get('capabilities'))
        available=[a for a in d.get('availability',[]) if a.get('region')==region]
        ondemand=any('ON_DEMAND' in enum_values(field(a,'servingModes','serving_modes',[])) and not past(field(a,'timeOnDemandRetired','time_on_demand_retired')) for a in available)
        fmt='COHEREV2' if 'COHERE' in vendor.upper() else 'GENERIC'
        compatible=any(v in vendor.upper() for v in ('COHERE','META','OPENAI'))
        access=field(d,'modelAccess','model_access','UNKNOWN')
        reason=''
        if 'CHAT' not in caps: reason='Not a chat model'
        elif item.get('type','BASE')!='BASE': reason='Requires a dedicated endpoint'
        elif not ondemand: reason='On-demand availability not verified in this region'
        elif past(field(item,'timeOnDemandRetired','time_on_demand_retired')): reason='Retired for on-demand inference'
        elif not compatible: reason='Requires another inference API adapter'
        elif access=='PROXY' and not allow_proxy: reason='External provider access is not enabled'
        elif access not in {'HOSTED','PROXY'}: reason='Model hosting location could not be verified'
        rows.append({'id':'oci-'+hashlib.sha256((region+mid).encode()).hexdigest()[:20],
            'label':label,'vendor':vendor,'region':region,'model_id':mid,'api_format':fmt,
            'enabled':not reason,'reason':reason,'access':access,'source':'oci',
            'capabilities':sorted(caps),'tool_support':'Verify with a connection check before use'})
    for i,d in enumerate(discovery):
        if i in matched: continue
        mid=field(d,'modelId','model_id','Unknown model')
        rows.append({'id':'oci-'+hashlib.sha256((region+mid).encode()).hexdigest()[:20],
            'label':mid,'vendor':d.get('vendor','Unknown'),'region':region,'model_id':'',
            'api_format':'','enabled':False,'reason':'Requires an inference API or endpoint not configured in this assistant',
            'access':field(d,'modelAccess','model_access','UNKNOWN'),'source':'oci',
            'capabilities':sorted(enum_values(d.get('capabilities'))),'tool_support':'Unavailable with the current adapter'})
    unique={r['id']:r for r in rows}
    return sorted(unique.values(),key=lambda r:(not r['enabled'],r['vendor'].lower(),r['label'].lower()))


class OfferedModels:
    def __init__(self,settings):
        self.settings=settings
        self.rows=[]; self.updated=None; self.error=None; self.lock=asyncio.Lock()
        self.source='demo' if settings.mode=='demo' else 'oci'

    def demo(self):
        rows=list(ModelCatalog(self.settings).models.values())
        for r in rows: r.update(source='demo',reason='',api_format='GENERIC')
        for key,label,vendor,fmt in [('demo-command-a','Cohere Command A','Cohere','COHEREV2'),('demo-llama','Llama 3.3 70B','Meta','GENERIC')]:
            rows.append({'id':key,'label':label,'region':self.settings.region,'model_id':'demo-only',
                'enabled':True,'vendor':vendor,'api_format':fmt,'source':'demo','reason':''})
        return rows

    async def refresh(self,force=False):
        async with self.lock:
            if self.updated and (time.time()-self.updated < (15 if force else 300)):
                return self.public()
            if self.settings.mode=='demo':
                self.rows=self.demo(); self.updated=time.time(); self.error=None
                return self.public()
            try:
                config=self.settings.load('mcp.json')
                if 'model_catalog' not in config: raise ValueError('Missing model catalog MCP configuration')
                async with asyncio.timeout(100):
                    async with MCPClients(config,self.settings.data_dir/'catalog'/secrets.token_hex(10)) as clients:
                        payload=await clients.call('model_catalog','list_offered_models',{})
                if payload.get('region')!=self.settings.region:
                    raise ValueError('Catalog returned a different region')
                self.rows=normalize_catalog(payload)
                self.updated=time.time(); self.error=None
            except Exception:
                self.error='OCI catalog could not be refreshed. Check the model-catalog MCP, OCI credentials and model discovery permissions.'
            return self.public()

    def public(self):
        rows=self.apply_policy()
        default=next((r['id'] for r in rows if r.get('enabled') and r.get('model_id')==self.settings.model_id),None)
        if not default:
            configured=ModelCatalog(self.settings).default
            default=next((r['id'] for r in rows if r['id']==configured and r.get('enabled')),None)
        if not default: default=next((r['id'] for r in rows if r.get('enabled')),'')
        keys={'id','label','region','enabled','reason','vendor','capabilities','access','source','tool_support'}
        return {'models':[{k:v for k,v in r.items() if k in keys} for r in rows],
            'default_model':default,'source':self.source,'region':self.settings.region,
            'updated_at':datetime.fromtimestamp(self.updated,timezone.utc).isoformat() if self.updated else None,
            'error':self.error,'stale':bool(self.error)}

    def apply_policy(self):
        rows=[dict(r) for r in self.rows]
        if self.settings.mode=='demo': return rows
        path=self.settings.config_dir/'models.json'
        config=self.settings.load('models.json') if path.exists() else {}
        allowed=config.get('allowed_model_ids')
        blocked=config.get('blocked_model_ids',[])
        if (allowed is not None and (not isinstance(allowed,list) or not all(isinstance(x,str) for x in allowed))) or not isinstance(blocked,list):
            raise ValueError('Invalid model access policy')
        for row in rows:
            if (allowed is not None and row['model_id'] not in allowed) or row['model_id'] in blocked:
                row.update(enabled=False,reason='Not approved by the administrator')
        return rows

    async def resolve(self,key):
        await self.refresh()
        if self.error: raise ValueError('Refresh the OCI model catalog successfully before starting an investigation.')
        chosen=next((r for r in self.apply_policy() if r['id']==(key or self.public()['default_model'])),None)
        if not chosen or not chosen['enabled']: raise ValueError('Choose an available OCI chat model from the refreshed catalog.')
        return dict(chosen)
