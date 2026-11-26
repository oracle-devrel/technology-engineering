import asyncio
import json
import os
import socket
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock,patch

import httpcore
import httpx
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from httpx import ASGITransport,AsyncClient

from assistant.connections import (ConnectionRegistry,ConnectionInput,EnvironmentInput,ConnectionError,
    environment_binding,environment_sources)
from assistant.remote_transport import PublicBackend,PublicTransport,validate_remote_url
from assistant.settings import Settings
from assistant.policy import allowed_environments
from assistant.web import create_app
from assistant.store import Store,ConversationScopeError

TENANT='ocid1.tenancy.oc1..tenantaaaaaaaa'
OTHER='ocid1.tenancy.oc1..tenantbbbbbbbb'
CID='ocid1.compartment.oc1..compartmentaaaa'
USER_ID='ocid1.user.oc1..useraaaaaaaa'
PROFILE={'tenancy':TENANT,'user':USER_ID,'fingerprint':'00:11','key_file':'/operator/key.pem','region':'eu-frankfurt-1'}
ADMIN={'sub':'admin','name':'Admin','groups':[]}


def fixture(folder):
 p=Path(folder);(p/'access.json').write_text(json.dumps({'administrators':{'subjects':['admin']},'environments':{}}));(p/'mcp.json').write_text(json.dumps({
  'identity':{'command':'/opt/app/bin/python'},'db':{'command':'/opt/db/bin/server'},'logan':{'command':'/opt/logan/bin/python'},'model_catalog':{'command':'catalog'}}))
 return Settings(mode='live',base_url='https://assistant.example.com',issuer='https://login.example.com',client_id='client',client_secret='secret',genai_compartment=CID,session_secret='s'*40,data_dir=p/'data',config_dir=p)


def connection(kind='db',**kw):
 return ConnectionInput(label='Tenant A '+kind,kind=kind,test_compartment_id=CID,namespace='test_namespace' if kind=='logan' else '',**kw)


class RegistryTests(unittest.TestCase):
 def setUp(self):
  self.folder=tempfile.TemporaryDirectory();self.s=fixture(self.folder.name)
  self.env=patch.dict(os.environ,{'CONNECTION_ENCRYPTION_KEY':Fernet.generate_key().decode()});self.env.start()
  self.profile=patch('assistant.connections.oci.config.from_file',return_value=PROFILE);self.profile.start();self.r=ConnectionRegistry(self.s)
 def tearDown(self):self.profile.stop();self.env.stop();self.folder.cleanup()
 def ready(self,kind='db'):
  c=self.r.create(connection(kind),'admin');self.r.test_result(c['id'],'admin',True);return self.r.get(c['id'])
 def test_credential_encryption_and_no_secret_echo(self):
  key=rsa.generate_private_key(public_exponent=65537,key_size=2048)
  pem=key.private_bytes(serialization.Encoding.PEM,serialization.PrivateFormat.PKCS8,serialization.NoEncryption()).decode()
  body=connection(auth_mode='api_key',private_key=pem,tenancy_id=TENANT,user_id=USER_ID,region='eu-frankfurt-1',transport='https',url='https://mcp.example.com/mcp',bearer_token='private-token-never-echo')
  public=self.r.create(body,'admin');raw=self.r.path.read_bytes();self.assertNotIn(pem.encode(),raw);self.assertNotIn(b'private-token-never-echo',raw)
  self.assertNotIn('private_key',json.dumps(public));self.assertNotIn('private-token-never-echo',json.dumps(self.r.list_connections()))
  self.assertEqual(self.r.get(public['id'],private=True)[1]['private_key'],pem)
  with patch.dict(os.environ,{'CONNECTION_ENCRYPTION_KEY':Fernet.generate_key().decode()}):
   with self.assertRaises(ConnectionError):ConnectionRegistry(self.s).get(public['id'],private=True)
 def test_tenant_region_kind_and_test_state_are_required_for_environment(self):
  db=self.ready();log=self.ready('logan')
  body=EnvironmentInput(label='New environment',compartment_id=CID,db_connection_id=db['id'],logan_connection_id=log['id'],subjects=['reader'])
  env=self.r.save_environment(body,'admin','Target');policy=self.s.load('access.json')
  self.assertIn(env['id'],allowed_environments(policy,{'sub':'reader','groups':[]}));self.assertEqual(allowed_environments(policy,{'sub':'outsider','groups':[]}),{})
  self.assertEqual(environment_sources(env),{'db','logan'})
  previous=environment_binding(policy['environments'][env['id']]);self.r.set_enabled(db['id'],False,'admin')
  self.assertNotIn(env['id'],self.s.load('access.json')['environments'])
  self.r.set_enabled(db['id'],True,'admin');self.assertNotEqual(previous,environment_binding(self.s.load('access.json')['environments'][env['id']]))
  with patch('assistant.connections.oci.config.from_file',return_value={**PROFILE,'tenancy':OTHER}):other=self.r.create(connection('logan'),'admin')
  self.r.test_result(other['id'],'admin',True)
  with self.assertRaises(ConnectionError):self.r.environment_connections(body.model_copy(update={'logan_connection_id':other['id']}))
  with self.assertRaises(ConnectionError):self.r.save_environment(body,'admin','Target',identifier='lab')
 def test_managed_runtime_uses_explicit_profile_and_cleans_material(self):
  db=self.ready();env={'compartment_id':CID,'tenancy_id':TENANT,'region':PROFILE['region'],'connection_refs':{'db':db['id']}}
  with self.r.runtime_config(self.s.load('mcp.json'),env,self.s.data_dir/'run') as cfg:
   self.assertNotIn('logan',cfg);self.assertEqual(cfg['db']['command'],'/opt/db/bin/server')
   path=Path(cfg['db']['env']['OCI_CONFIG_FILE']);self.assertTrue(path.exists());self.assertEqual(path.stat().st_mode&0o777,0o600)
   self.assertEqual(cfg['identity']['env']['OCI_CONFIG_FILE'],str(path));self.assertTrue(cfg['db']['isolate_oci_env'])
   self.assertEqual(cfg['db']['env']['OCI_CONFIG_PROFILE'],'DEFAULT')
  self.assertFalse(path.exists())
  with patch('assistant.connections.oci.config.from_file',return_value={**PROFILE,'tenancy':OTHER}):
   with self.assertRaises(ConnectionError):
    with self.r.runtime_config(self.s.load('mcp.json'),env,self.s.data_dir/'changed'):pass
 def test_connection_change_requires_new_conversation(self):
  st=Store(self.s.data_dir/'test.sqlite3');rid=st.create_run('reader','env','First question',30,compartment_id=CID,connection_binding='version1')
  cid=st.get(rid,'reader')['conversation_id'];st.update(rid,status='complete',answer='Prior evidence')
  with self.assertRaises(ConversationScopeError):st.create_run('reader','env','Follow up',30,conversation_id=cid,compartment_id=CID,connection_binding='version2')
 def test_no_key_no_plaintext_registration_and_no_arbitrary_command(self):
  with patch.dict(os.environ,{'CONNECTION_ENCRYPTION_KEY':''}):
   with self.assertRaises(ConnectionError):ConnectionRegistry(self.s).create(connection(),'admin')
  with self.assertRaises(Exception):ConnectionInput.model_validate({**connection().model_dump(),'command':'run-anything'})


class NetworkTests(unittest.IsolatedAsyncioTestCase):
 def test_rejects_local_insecure_and_embedded_credentials_urls(self):
  for url in ['http://mcp.example.com/','https://127.0.0.1/mcp','https://169.254.169.254/','https://[::1]/mcp','https://user:password@mcp.example.com/','https://mcp.example.com/mcp?key=secret','https://mcp.example.com:8443/','https://224.0.0.1/']:
   with self.assertRaises(ValueError):validate_remote_url(url)
  self.assertEqual(validate_remote_url('https://mcp.example.com/mcp'),'https://mcp.example.com/mcp')
 async def test_socket_pins_checked_public_address_and_rejects_mixed_dns(self):
  b=PublicBackend();b.backend=SimpleNamespace(connect_tcp=AsyncMock(return_value='stream'))
  loop=asyncio.get_running_loop()
  def record(ip):return (socket.AF_INET,socket.SOCK_STREAM,6,'',(ip,443))
  with patch.object(loop,'getaddrinfo',new=AsyncMock(return_value=[record('8.8.8.8')])):
   self.assertEqual(await b.connect_tcp('mcp.example.com',443),'stream')
  self.assertEqual(b.backend.connect_tcp.call_args.args[0],'8.8.8.8');b.backend.connect_tcp.reset_mock()
  with patch.object(loop,'getaddrinfo',new=AsyncMock(return_value=[record('8.8.8.8'),record('127.0.0.1')])):
   with self.assertRaises(httpcore.ConnectError):await b.connect_tcp('mcp.example.com',443)
  b.backend.connect_tcp.assert_not_called()
 async def test_tls_sni_remains_hostname_while_socket_uses_verified_ip(self):
  calls=[]
  class Stream(httpcore.AsyncNetworkStream):
   async def start_tls(self,ssl_context,server_hostname=None,timeout=None):calls.append(('sni',server_hostname));return self
   async def write(self,buffer,timeout=None):pass
   async def read(self,max_bytes,timeout=None):return b'HTTP/1.1 200 OK\r\nContent-Length: 2\r\nConnection: close\r\n\r\nOK'
   async def aclose(self):pass
  async def connect(host,*args,**kw):calls.append(('ip',host));return Stream()
  transport=PublicTransport();transport._pool._network_backend.backend=SimpleNamespace(connect_tcp=connect)
  loop=asyncio.get_running_loop();record=(socket.AF_INET,socket.SOCK_STREAM,6,'',('8.8.8.8',443))
  with patch.object(loop,'getaddrinfo',new=AsyncMock(return_value=[record])):
   async with httpx.AsyncClient(transport=transport,trust_env=False) as client:
    response=await client.get('https://mcp.example.com/mcp');self.assertEqual(response.text,'OK')
  self.assertIn(('ip','8.8.8.8'),calls);self.assertIn(('sni','mcp.example.com'),calls)


class AdminWebTests(unittest.IsolatedAsyncioTestCase):
 async def asyncSetUp(self):
  self.folder=tempfile.TemporaryDirectory();self.s=fixture(self.folder.name)
  self.key=patch.dict(os.environ,{'CONNECTION_ENCRYPTION_KEY':Fernet.generate_key().decode()});self.key.start()
  self.profile=patch('assistant.connections.oci.config.from_file',return_value=PROFILE);self.profile.start()
  self.verify=patch('assistant.web.verify_connection',new=AsyncMock(return_value={'compartment_name':'Target'}));self.mock_verify=self.verify.start()
  self.app=create_app(self.s);self.client=AsyncClient(transport=ASGITransport(app=self.app),base_url=self.s.base_url)
  self.client.cookies.set('db_session',self.app.state.store.session(ADMIN));me=(await self.client.get('/api/me')).json();self.headers={'origin':self.s.base_url,'x-csrf-token':me['csrf']}
 async def asyncTearDown(self):
  await self.client.aclose();self.verify.stop();self.profile.stop();self.key.stop();self.folder.cleanup()
 async def test_admin_can_register_test_bind_and_disable_without_credential_echo(self):
  data=connection().model_dump(mode='json');data.pop('private_key');data.pop('key_passphrase');data.pop('bearer_token')
  response=await self.client.post('/api/admin/connections',json=data,headers=self.headers);self.assertEqual(response.status_code,202,response.text)
  identifier=response.json()['id'];await asyncio.sleep(.03)
  state=(await self.client.get('/api/admin/configuration')).json();self.assertEqual(state['connections'][0]['status'],'ready');self.assertNotIn('encrypted',response.text)
  body={'label':'Target env','compartment_id':CID,'db_connection_id':identifier,'subjects':['admin']}
  response=await self.client.post('/api/admin/environments',json=body,headers=self.headers);self.assertEqual(response.status_code,200,response.text)
  me=(await self.client.get('/api/me')).json();self.assertEqual(me['environments'][0]['available_mcps'],['db'])
  response=await self.client.post('/api/admin/connections/'+identifier+'/enabled',json={'enabled':False},headers=self.headers);self.assertEqual(response.status_code,200)
  self.assertEqual((await self.client.get('/api/me')).json()['environments'],[])
 async def test_non_admin_csrf_and_validation_errors_cannot_leak_secrets(self):
  payload={'label':'Secret','kind':'db','test_compartment_id':CID,'private_key':{'sensitive':'never-echo-this-value'}}
  response=await self.client.post('/api/admin/connections',json=payload,headers=self.headers);self.assertEqual(response.status_code,422);self.assertNotIn('never-echo',response.text)
  data={'label':'Test','kind':'db','test_compartment_id':CID}
  response=await self.client.post('/api/admin/connections',json=data,headers={**self.headers,'x-csrf-token':'wrong'});self.assertEqual(response.status_code,403)
  reader={'sub':'reader','name':'Reader','groups':[]};self.client.cookies.set('db_session',self.app.state.store.session(reader));me=(await self.client.get('/api/me')).json()
  self.assertFalse(me['is_admin']);self.assertEqual((await self.client.get('/api/admin/configuration')).status_code,403)
  response=await self.client.post('/api/admin/connections',json=data,headers={'origin':self.s.base_url,'x-csrf-token':me['csrf']});self.assertEqual(response.status_code,403)
  self.mock_verify.assert_not_called()

class ConnectionServiceTests(unittest.IsolatedAsyncioTestCase):
 async def test_db_test_requires_read_only_scope_and_disables_subtree(self):
  from assistant.connection_service import check_data_path
  contract={'name':'list_managed_databases','mutable':False,'inputSchema':{'type':'object','properties':{'compartment_id':{'type':'string'},'limit':{'type':'integer'},'compartment_id_in_subtree':{'type':'boolean'}},'required':['compartment_id']}}
  clients=SimpleNamespace(connect=AsyncMock(),schemas={'db':{k:{} for k in ['list_dbo_skills','list_dbo_tools','describe_dbo_tool','invoke_dbo_tool']}},call=AsyncMock(side_effect=[contract,{}]))
  await check_data_path(clients,'db',CID)
  self.assertEqual(clients.call.await_args_list[1].args,('db','invoke_dbo_tool',{'tool_name':'list_managed_databases','arguments':{'compartment_id':CID,'limit':1,'compartment_id_in_subtree':False}}))
  contract['mutable']=True;clients.call=AsyncMock(return_value=contract)
  with self.assertRaises(ConnectionError):await check_data_path(clients,'db',CID)
  self.assertEqual(clients.call.await_count,1)
 async def test_logan_test_uses_only_bounded_scoped_query(self):
  from assistant.connection_service import check_data_path
  schema={'type':'object','properties':{k:{} for k in ['compartment_id','include_subcompartments','time_start','time_end','query','max_results']}}
  clients=SimpleNamespace(connect=AsyncMock(),schemas={'logan':{'run_query':schema}},call=AsyncMock(return_value={}))
  await check_data_path(clients,'logan',CID)
  server,tool,args=clients.call.await_args.args
  self.assertEqual((server,tool),('logan','run_query'));self.assertEqual(args['compartment_id'],CID);self.assertIs(args['include_subcompartments'],False);self.assertEqual(args['query'],'* | stats count');self.assertEqual(args['max_results'],1)
  from datetime import datetime,timedelta
  self.assertEqual(datetime.fromisoformat(args['time_end'])-datetime.fromisoformat(args['time_start']),timedelta(minutes=15))
  del schema['properties']['include_subcompartments']
  with self.assertRaises(ConnectionError):await check_data_path(clients,'logan',CID)
  self.assertEqual(clients.call.await_count,1)
