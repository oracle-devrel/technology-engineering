import asyncio
import hmac
import json
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path

from authlib.integrations.starlette_client import OAuth
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from starlette.middleware.sessions import SessionMiddleware

from .agent import SKILL_NAMES, investigate
from .policy import PolicyError, allowed_environments, authorize_environment, environment_options, redact, timestamps
from .settings import ROOT, Settings
from .models import ModelCatalog
from .offered_models import OfferedModels
from .store import Store,ConversationScopeError
from . import telemetry
from .gateway import DB_OPERATIONS
from .routing import route,routing_options
from .connections import ConnectionRegistry,ConnectionInput,EnvironmentInput,ConnectionError as RegistryConnectionError,admin_allowed,environment_binding,environment_sources,ocid
from .connection_service import verify_connection,safe_connection_error


class Question(BaseModel):
    question: str = Field(min_length=3,max_length=4000)
    environment: str = Field(max_length=100)
    skill: str = 'auto'
    hours: int = Field(default=1,ge=1,le=168)
    model: str = Field(default='',max_length=64)
    conversation_id: str = Field(default='',max_length=32,pattern=r'^(|[a-f0-9]{32})$')
    preferred_mcp: str = Field(default='auto',max_length=32)
    preferred_tool: str = Field(default='auto',max_length=100)


def create_app(settings=None):
    s = settings or Settings()
    s.validate()
    s.load('access.json')
    s.load('mcp.json')
    ModelCatalog(s)
    offered = OfferedModels(s)
    store = Store(s.data_dir/'assistant.sqlite3')
    registry=ConnectionRegistry(s)
    for pending in registry.list_connections():
        if pending['status']=='pending':registry.test_result(pending['id'],'system',False,'The assistant restarted before the test finished. Retest this connection.')
    connection_tasks={}
    connection_semaphore=asyncio.Semaphore(2)
    tasks = set()
    semaphore = asyncio.Semaphore(s.max_concurrent)
    tracing=telemetry.configure(s)

    @asynccontextmanager
    async def lifespan(app):
        yield
        for task in tasks:
            task.cancel()
        for task in connection_tasks.values():task.cancel()
        await asyncio.gather(*tasks,*connection_tasks.values(),return_exceptions=True)
        await asyncio.to_thread(telemetry.shutdown)

    app = FastAPI(title='DB Assistant',lifespan=lifespan,docs_url=None,redoc_url=None,openapi_url=None)
    @app.exception_handler(RequestValidationError)
    async def invalid_request(request,exc):
        # Pydantic's default response can echo a submitted private key or bearer token.
        return JSONResponse({'detail':'Request fields failed validation. Check the required fields and their formats.'},status_code=422)
    secure = s.mode == 'live'
    app.add_middleware(SessionMiddleware,secret_key=s.session_secret,session_cookie='db_oauth_state',
        https_only=secure,same_site='lax',max_age=600)
    oauth = OAuth()
    if secure:
        oauth.register('company',client_id=s.client_id,client_secret=s.client_secret,
            server_metadata_url=s.issuer+'/.well-known/openid-configuration',
            client_kwargs={'scope':'openid profile email','code_challenge_method':'S256'})

    @app.middleware('http')
    async def security_headers(request,call_next):
        response = await call_next(request)
        response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Referrer-Policy'] = 'no-referrer'
        response.headers['Cache-Control'] = 'no-store'
        if secure:
            response.headers['Strict-Transport-Security'] = 'max-age=31536000'
        return response

    def current(request):
        token = request.cookies.get('db_session','')
        result = store.user(token) if token else None
        if not result:
            raise HTTPException(401,'Sign in to continue')
        return result

    def csrf(request):
        user, token = current(request)
        if request.headers.get('origin') != s.base_url or not hmac.compare_digest(request.headers.get('x-csrf-token',''),token):
            raise HTTPException(403,'Invalid request origin or CSRF token')
        return user

    def signed_in(user):
        token = store.session(user)
        response = RedirectResponse('/',status_code=303)
        response.set_cookie('db_session',token,httponly=True,secure=secure,samesite='lax',max_age=28800,path='/')
        return response

    def configuration_admin(request,write=False):
        user=csrf(request) if write else current(request)[0]
        if not admin_allowed(s.load('access.json'),user):raise HTTPException(403,'Configuration administrator access is required')
        return user

    @app.get('/configuration')
    async def configuration(request:Request):
        configuration_admin(request)
        return FileResponse(ROOT/'static'/'configuration.html')

    @app.get('/api/admin/configuration')
    async def configuration_state(request:Request):
        user=configuration_admin(request)
        return {'connections':registry.list_connections(),'environments':registry.list_environments(),
            'profiles':registry.profile_names(),'credentials_ready':registry.cipher is not None,'subject':user['sub'],
            'demo':s.mode=='demo','genai_region':s.region,
            'lifecycle':'Managed servers start for tests and investigations, then stop. HTTPS mode connects to an already-running server.'}

    async def test_connection_job(identifier,actor):
        try:
            async with connection_semaphore:
                evidence=await verify_connection(registry,identifier)
                registry.test_result(identifier,actor,True)
        except asyncio.CancelledError:
            registry.test_result(identifier,actor,False,'The assistant restarted during the test. Retest this connection.')
            raise
        except Exception as exc:registry.test_result(identifier,actor,False,safe_connection_error(exc))

    def start_connection_test(identifier,actor):
        if len(connection_tasks)>=4:raise HTTPException(429,'Connection tests are busy. Try again shortly.')
        if identifier in connection_tasks:raise HTTPException(409,'This connection is already being tested')
        registry.mark_testing(identifier,actor)
        task=asyncio.create_task(test_connection_job(identifier,actor));connection_tasks[identifier]=task
        task.add_done_callback(lambda done:connection_tasks.pop(identifier,None))

    @app.post('/api/admin/connections',status_code=202)
    async def add_connection(body:ConnectionInput,request:Request):
        user=configuration_admin(request,True)
        if s.mode=='demo':raise HTTPException(400,'Connection setup is disabled in demo mode')
        if len(connection_tasks)>=4:raise HTTPException(429,'Connection tests are busy. Try again shortly.')
        try:public=registry.create(body,user['sub'])
        except RegistryConnectionError as exc:raise HTTPException(400,str(exc)) from None
        start_connection_test(public['id'],user['sub'])
        return public

    @app.post('/api/admin/connections/{identifier}/test',status_code=202)
    async def test_connection(identifier:str,request:Request):
        user=configuration_admin(request,True)
        if s.mode=='demo':raise HTTPException(400,'Connection setup is disabled in demo mode')
        try:
            item=registry.get(identifier)
            if not item['enabled']:raise RegistryConnectionError('Enable the connection before testing it')
        except RegistryConnectionError as exc:raise HTTPException(400,str(exc)) from None
        start_connection_test(identifier,user['sub']);return {'id':identifier,'status':'testing'}

    @app.post('/api/admin/connections/{identifier}/enabled')
    async def enable_connection(identifier:str,request:Request):
        user=configuration_admin(request,True)
        body=await request.json()
        if not isinstance(body,dict) or type(body.get('enabled')) is not bool:raise HTTPException(400,'Provide enabled as true or false')
        try:return registry.set_enabled(identifier,body['enabled'],user['sub'])
        except RegistryConnectionError as exc:raise HTTPException(400,str(exc)) from None

    async def assign_environment(body,request,identifier=None):
        user=configuration_admin(request,True)
        if s.mode=='demo':raise HTTPException(400,'Connection setup is disabled in demo mode')
        try:
            ocid(body.compartment_id,'compartment')
            if identifier is not None and not any(e['id']==identifier for e in registry.list_environments()):raise RegistryConnectionError('Additional environment not found')
            selected=registry.environment_connections(body)
            names=[]
            async with connection_semaphore:
                for item in selected.values():
                    verified=await verify_connection(registry,item['id'],body.compartment_id)
                    names.append(verified['compartment_name'])
            if len(set(names))!=1:raise RegistryConnectionError('Connections returned different compartment identities')
            return registry.save_environment(body,user['sub'],names[0],identifier)
        except Exception as exc:raise HTTPException(400,safe_connection_error(exc)) from None

    @app.post('/api/admin/environments')
    async def add_environment(body:EnvironmentInput,request:Request):return await assign_environment(body,request)

    @app.put('/api/admin/environments/{identifier}')
    async def update_environment(identifier:str,body:EnvironmentInput,request:Request):return await assign_environment(body,request,identifier)

    @app.post('/api/admin/environments/{identifier}/disable')
    async def disable_environment(identifier:str,request:Request):
        user=configuration_admin(request,True)
        try:registry.disable_environment(identifier,user['sub']);return {'ok':True}
        except RegistryConnectionError as exc:raise HTTPException(400,str(exc)) from None

    @app.get('/auth/login')
    async def login(request:Request):
        if s.mode == 'demo':
            return signed_in({'sub':'demo-user','name':'Demo DBA','groups':['DBA-Observability']})
        return await oauth.company.authorize_redirect(request,s.base_url+'/auth/callback')

    @app.get('/auth/callback')
    async def callback(request:Request):
        if s.mode != 'live':
            raise HTTPException(404)
        try:
            token = await oauth.company.authorize_access_token(request)
            # Authlib verifies the ID token signature, issuer, audience, nonce and expiry.
            claims = token.get('userinfo')
            if not claims or not claims.get('sub'):
                raise ValueError('Missing verified OpenID subject')
            groups = claims.get(s.groups_claim,[])
            if not isinstance(groups,list) or any(not isinstance(g,str) for g in groups):
                raise ValueError('Expected a list-valued group claim')
            user = {'sub':claims['sub'],'name':claims.get('name','DBA'),'groups':groups}
            request.session.clear()
            return signed_in(user)
        except Exception:
            request.session.clear()
            raise HTTPException(401,'Company sign-in failed. Ask the administrator to check the OIDC registration and group claim.')

    @app.post('/auth/logout')
    async def logout(request:Request):
        csrf(request)
        store.logout(request.cookies['db_session'])
        response = JSONResponse({'ok':True})
        response.delete_cookie('db_session')
        return response

    @app.get('/api/me')
    async def me(request:Request):
        user, token = current(request)
        envs = allowed_environments(s.load('access.json'),user)
        return {'name':user['name'],'subject':user['sub'],'groups':user['groups'],'csrf':token,'mode':s.mode,
            'is_admin':admin_allowed(s.load('access.json'),user),
            **offered.public(),
            'routing_options':routing_options(DB_OPERATIONS),
            'environments':environment_options(s.load('access.json'),user)}

    def catalog_user(request,refresh=False):
        user = csrf(request) if refresh else current(request)[0]
        if not allowed_environments(s.load('access.json'),user):
            raise HTTPException(403,'No approved environments are assigned to your account')

    @app.get('/api/models')
    async def models(request:Request):
        catalog_user(request)
        return await offered.refresh()

    @app.post('/api/models/refresh')
    async def refresh_models(request:Request):
        catalog_user(request,refresh=True)
        return await offered.refresh(force=True)

    @app.post('/api/runs',status_code=202)
    async def submit(body:Question,request:Request):
        user = csrf(request)
        if len(tasks) >= s.max_concurrent*2:
            raise HTTPException(429,'The assistant is busy. Try again after the current investigations finish.')
        try:
            env = authorize_environment(s.load('access.json'),user,body.environment)
            try:
                selection = await offered.resolve(body.model)
            except ValueError as e:
                raise HTTPException(400,str(e))
            if body.skill != 'auto' and body.skill not in SKILL_NAMES:
                raise ValueError('Unknown workflow')
            window = timestamps(body.hours)
            question = redact(body.question.strip())
            try:routing=route(question,body.preferred_mcp,body.preferred_tool,DB_OPERATIONS,body.skill)
            except ValueError as e:raise HTTPException(400,str(e))
            if routing['conflict']:raise HTTPException(400,'Top SQL needs Database Observability MCP. Choose that source or Choose for me; Log Analytics cannot supply a SQL ranking.')
            sources=environment_sources(env)
            if routing['mcp']!='auto' and routing['mcp'] not in sources:
                raise HTTPException(400,'The requested MCP is not assigned to this environment. Select an available source or ask the configuration administrator.')
            if routing['mcp']=='auto' and len(sources)==1:routing['mcp']=next(iter(sources))
            rid = store.create_run(user['sub'],body.environment,question,s.daily_runs,model=selection,
                conversation_id=body.conversation_id or None,compartment_id=env['compartment_id'],window=window,routing=routing,connection_binding=environment_binding(env))
        except LookupError:
            raise HTTPException(404,'Conversation not found')
        except ConversationScopeError as e:
            raise HTTPException(400,str(e))
        except PolicyError as e:
            raise HTTPException(403,str(e))
        except ValueError as e:
            raise HTTPException(429,str(e))
        task = asyncio.create_task(investigate(s,store,rid,user,env,question,body.skill,window,semaphore,model_selection=selection))
        tasks.add(task)
        task.add_done_callback(tasks.discard)
        row=store.get(rid,user['sub'])
        return {'id':rid,'conversation_id':row['conversation_id'],'trace_id':row['trace_id']}

    @app.get('/api/conversations')
    async def conversations(request:Request):
        user,_=current(request)
        allowed=allowed_environments(s.load('access.json'),user)
        return [{k:r[k] for k in ('id','environment','title','created','updated','turn_count','trace_id')}
            for r in store.conversations(user['sub']) if r['environment'] in allowed and
            r['compartment_id']==allowed[r['environment']]['compartment_id']]

    @app.get('/api/conversations/{cid}')
    async def conversation(cid:str,request:Request):
        user,_=current(request)
        row=store.conversation(cid,user['sub'])
        if not row:raise HTTPException(404,'Conversation not found')
        try:env=authorize_environment(s.load('access.json'),user,row['environment'])
        except PolicyError:raise HTTPException(403,'Access to this environment is no longer granted')
        if env['compartment_id']!=row['compartment_id']:
            raise HTTPException(403,'The conversation environment has changed; start a new conversation')
        row.pop('owner',None);row['tracing_enabled']=tracing
        return row

    @app.get('/api/runs')
    async def history(request:Request):
        user,_ = current(request)
        return store.history(user['sub'])

    def own_run(rid,request):
        user,_ = current(request)
        row = store.get(rid,user['sub'])
        if not row:
            raise HTTPException(404,'Investigation not found')
        # Recheck environment policy even for historical answers.
        try:
            env=authorize_environment(s.load('access.json'),user,row['environment'])
            if row.get('conversation_compartment') and row['conversation_compartment']!=env['compartment_id']:
                raise PolicyError('Conversation scope changed')
        except PolicyError:
            raise HTTPException(403,'Access to this environment is no longer granted')
        return row

    @app.get('/api/runs/{rid}')
    async def result(rid:str,request:Request):
        return own_run(rid,request)

    @app.get('/api/runs/{rid}/report')
    async def report(rid:str,request:Request):
        r = own_run(rid,request)
        model = r['model']
        model_text = model.get('label','Not recorded (older investigation)')
        text = f"DB Assistant\nConversation: {r.get('conversation_id') or 'Legacy standalone report'}\nTrace ID: {r.get('trace_id') or 'Not recorded'}\nInteraction span: {r.get('interaction_span_id') or 'Not recorded'}\nInvestigation: {r['id']}\nEnvironment: {r['environment']}\nModel: {model_text}\nRegion: {model.get('region','Not recorded')}\nStatus: {r['status']}\n\n{r['question']}\n\n{r['answer']}\n\nTool timeline\n"+json.dumps(r['events'],indent=2)
        return Response(text,media_type='text/plain',headers={'Content-Disposition':'attachment; filename="db-assistant-report.txt"'})

    @app.get('/healthz')
    async def health():
        return {'status':'ok','mode':s.mode}

    @app.get('/')
    async def index():
        return FileResponse(ROOT/'static'/'index.html')

    app.mount('/static',StaticFiles(directory=ROOT/'static'),name='static')
    app.state.store = store
    return app
