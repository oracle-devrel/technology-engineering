"""OCI inference only. Observability data is retrieved exclusively through MCP."""
import asyncio
import json
import os
import oci
from .telemetry import traced
from opentelemetry import trace


class ModelResponseError(ValueError):
    """The provider returned no usable answer or function call after bounded recovery."""


def config_and_signer():
    mode = os.getenv("OCI_AUTH_TYPE", "api_key")
    region = os.getenv("OCI_REGION", "eu-frankfurt-1")
    if mode == "oke_workload_identity":
        return {"region": region}, oci.auth.signers.get_oke_workload_identity_resource_principal_signer()
    if mode == "instance_principal":
        return {"region": region}, oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
    if mode != "api_key":
        raise ValueError("Unsupported OCI_AUTH_TYPE")
    c = oci.config.from_file(os.getenv("OCI_CONFIG_FILE", "/secrets/oci/config"), os.getenv("OCI_CONFIG_PROFILE", "DEFAULT"))
    # Passing signer=None to an OCI client disables its default API-key signer.
    signer = oci.signer.Signer(tenancy=c['tenancy'], user=c['user'],
        fingerprint=c['fingerprint'], private_key_file_location=c.get('key_file'),
        pass_phrase=c.get('pass_phrase'), private_key_content=c.get('key_content'))
    return c, signer


class OCIModel:
    def __init__(self, settings, selection=None):
        self.settings = settings
        self.model_id = selection['model_id'] if selection else settings.model_id
        self.model_name = selection.get('label',self.model_id) if selection else self.model_id
        self.region = selection['region'] if selection else settings.region
        self.api_format = selection.get('api_format','GENERIC') if selection else 'GENERIC'
        config, signer = config_and_signer()
        self.client = oci.generative_ai_inference.GenerativeAiInferenceClient(
            config, signer=signer, timeout=(10,180 if self.api_format=='COHEREV2' else 90), retry_strategy=oci.retry.NoneRetryStrategy(),
            service_endpoint=f"https://inference.generativeai.{self.region}.oci.oraclecloud.com")
        self.m = oci.generative_ai_inference.models

    def message(self, role, text, tool_call_id=None):
        types = {'SYSTEM':self.m.SystemMessage, 'USER':self.m.UserMessage, 'ASSISTANT':self.m.AssistantMessage, 'TOOL':self.m.ToolMessage}
        kw = {'content':[self.m.TextContent(text=text)]}
        if tool_call_id:
            kw['tool_call_id'] = tool_call_id
        return types[role](**kw)

    async def chat(self, messages, definitions, require_tools=False):
        # Reasoning is not answer text. A reasoning-only response can exhaust the
        # output budget; retry once without adding that empty turn to the history.
        for attempt in range(2):
            result = await self._chat_once(messages, definitions, require_tools, attempt)
            if result.tool_calls or any((getattr(c,'text',None) or '').strip() for c in result.content or []):
                return result
        raise ModelResponseError('empty_model_response')

    @traced('genai.chat',lambda self,messages,definitions,require_tools,attempt:{'gen_ai.provider.name':'oci','gen_ai.operation.name':'chat','gen_ai.request.model':self.model_id,'cloud.region':self.region,'gen_ai.api_format':self.api_format,'gen_ai.request.attempt':attempt+1})
    async def _chat_once(self, messages, definitions, require_tools, attempt):
        max_tokens = 8192 if attempt else 4096
        if self.api_format == 'COHEREV2':
            types={'SYSTEM':self.m.CohereSystemMessageV2,'USER':self.m.CohereUserMessageV2,
                'ASSISTANT':self.m.CohereAssistantMessageV2,'TOOL':self.m.CohereToolMessageV2}
            translated=[]
            for message in messages:
                args={'content':[self.m.CohereTextContentV2(text=c.text) for c in (message.content or []) if hasattr(c,'text')]}
                if message.role=='TOOL': args['tool_call_id']=message.tool_call_id
                if message.role=='ASSISTANT' and message.tool_calls:
                    args['tool_calls']=[self.m.CohereToolCallV2(id=c.id,type='FUNCTION',function={'name':c.name,'arguments':c.arguments}) for c in message.tool_calls]
                    args['tool_plan']=message.reasoning_content
                translated.append(types[message.role](**args))
            request=self.m.CohereChatRequestV2(messages=translated,
                tools=[self.m.CohereToolV2(type='FUNCTION',function=self.m.Function(**t)) for t in definitions],max_tokens=max_tokens,temperature=0.1)
            if require_tools: request.tools_choice='REQUIRED'
        else:
            request = self.m.GenericChatRequest(messages=messages, tools=[self.m.FunctionDefinition(**t) for t in definitions],
                is_parallel_tool_calls=False, max_tokens=max_tokens, temperature=0.1)
            if self.model_name.startswith('openai.gpt-oss-') or self.model_id.startswith('openai.gpt-oss-'):
                request.reasoning_effort = 'LOW'
            if require_tools: request.tool_choice=self.m.ToolChoiceRequired()
        details = self.m.ChatDetails(compartment_id=self.settings.genai_compartment,
            serving_mode=self.m.OnDemandServingMode(model_id=self.model_id), chat_request=request)
        response = await asyncio.to_thread(self.client.chat, details)
        chat=response.data.chat_response
        current = trace.get_current_span()
        finish = getattr(chat,'finish_reason',None) if self.api_format=='COHEREV2' else getattr(chat.choices[0],'finish_reason',None) if chat.choices else None
        if finish:
            current.set_attribute('gen_ai.response.finish_reasons',[finish if finish in {'stop','length','tool_calls','STOP','MAX_TOKENS','COMPLETE','ERROR'} else 'other'])
        if self.api_format=='COHEREV2':
            message=chat.message
            calls=[self.m.FunctionCall(id=c.id,name=c.function['name'],arguments=c.function['arguments'] if isinstance(c.function['arguments'],str) else json.dumps(c.function['arguments'])) for c in (message.tool_calls or [])]
            return self.m.AssistantMessage(content=[self.m.TextContent(text=c.text) for c in (message.content or []) if hasattr(c,'text')],tool_calls=calls,reasoning_content=message.tool_plan)
        if not chat.choices or chat.choices[0].message is None:
            return self.m.AssistantMessage(content=[])
        return chat.choices[0].message
