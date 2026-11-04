"""Metadata-only conversation traces; prompts, tool arguments and errors are never exported."""
import asyncio
import functools
import inspect
import logging
import os
from contextlib import contextmanager
from contextvars import ContextVar
from urllib.parse import urlsplit

from opentelemetry import trace
from opentelemetry.context import Context
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.id_generator import RandomIdGenerator
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.trace import NonRecordingSpan, SpanContext, TraceFlags, Status, StatusCode

_root_ids=ContextVar('conversation_root_ids',default=None)
_provider=trace.NoOpTracerProvider()
_enabled=False
log=logging.getLogger(__name__)

class ConversationIds(RandomIdGenerator):
    def generate_trace_id(self):
        return _root_ids.get()[0] if _root_ids.get() else super().generate_trace_id()
    def generate_span_id(self):
        return _root_ids.get()[1] if _root_ids.get() else super().generate_span_id()

class Exporter(OTLPSpanExporter):
    def export(self, spans):
        # Do not log exceptions from the HTTP exporter: transport details may contain credentials.
        try:
            result=super().export(spans)
            log.info('APM export service=db-assistant spans=%d result=%s',len(spans),result.name)
            return result
        except Exception as exc:
            from opentelemetry.sdk.trace.export import SpanExportResult
            log.warning('APM export failed error_type=%s',type(exc).__name__)
            return SpanExportResult.FAILURE

def configure(settings, exporter=None):
    global _provider,_enabled
    endpoint=os.getenv('APM_TRACES_ENDPOINT','');key=os.getenv('APM_DATA_KEY','')
    if exporter is None and (settings.mode!='live' or not endpoint or not key):return False
    parsed=urlsplit(endpoint)
    if exporter is None and (parsed.scheme!='https' or not parsed.hostname or '.apm-agt.' not in parsed.hostname
            or not parsed.hostname.endswith('.oci.oraclecloud.com') or parsed.username):
        raise ValueError('APM requires an approved OCI HTTPS ingestion endpoint')
    provider=TracerProvider(resource=Resource.create({'service.name':'db-assistant','service.version':'0.2.0',
        'deployment.environment.name':'lab','cloud.provider':'oci','cloud.region':settings.region,
        'k8s.namespace.name':'db-assistant','k8s.pod.name':os.getenv('HOSTNAME','')}),id_generator=ConversationIds())
    if exporter is None:exporter=Exporter(endpoint=endpoint,headers={'Authorization':'dataKey '+key},timeout=15)
    provider.add_span_processor(BatchSpanProcessor(exporter,schedule_delay_millis=1000))
    _provider=provider;_enabled=True
    return True

def shutdown():
    global _provider,_enabled
    _provider.shutdown() if hasattr(_provider,'shutdown') else None
    _provider=trace.NoOpTracerProvider();_enabled=False

def flush():
    return _provider.force_flush(timeout_millis=20000) if _enabled else True

def enabled():return _enabled

@contextmanager
def span(name,attributes=None,parent=None):
    with _provider.get_tracer('db-assistant').start_as_current_span(name,context=parent,
            attributes=attributes or {},record_exception=False,set_status_on_exception=False) as current:
        try:yield current
        except BaseException as exc:
            current.set_attribute('error.type',type(exc).__name__)
            current.set_status(Status(StatusCode.ERROR,type(exc).__name__))
            raise

def traced(name, attributes=lambda *a,**kw:{}):
    def decorate(fn):
        if inspect.iscoroutinefunction(fn):
            @functools.wraps(fn)
            async def call(*a,**kw):
                with span(name(*a,**kw) if callable(name) else name,attributes(*a,**kw)):return await fn(*a,**kw)
        else:
            @functools.wraps(fn)
            def call(*a,**kw):
                with span(name(*a,**kw) if callable(name) else name,attributes(*a,**kw)):return fn(*a,**kw)
        return call
    return decorate

@contextmanager
def interaction(row,store):
    attributes={'conversation.id':row.get('conversation_id') or '', 'interaction.id':row['id'],
        'interaction.turn':row.get('turn_index',1),'environment.id':row['environment']}
    parent=None
    if row.get('trace_id') and row.get('root_span_id'):
        ids=(int(row['trace_id'],16),int(row['root_span_id'],16))
        if _enabled and not row.get('root_emitted'):
            token=_root_ids.set(ids)
            try:
                # Root marks creation; persisted parent IDs let later turns join the trace
                # without holding an unfinished span in memory across process restarts.
                root=_provider.get_tracer('db-assistant').start_span('dbassistant.conversation',context=Context(),
                    attributes={'conversation.id':row['conversation_id'],'environment.id':row['environment']},
                    start_time=int(row['conversation_created']*1e9))
            finally:_root_ids.reset(token)
            root.end(end_time=int(row['conversation_created']*1e9)+1000)
            store.mark_root_emitted(row['conversation_id'])
        if _enabled:parent=trace.set_span_in_context(NonRecordingSpan(SpanContext(*ids,is_remote=False,trace_flags=TraceFlags(1))),Context())
    with span('dbassistant.interaction',attributes,parent) as current:
        if _enabled and current.get_span_context().is_valid:
            store.update(row['id'],interaction_span_id=format(current.get_span_context().span_id,'016x'))
        yield current
