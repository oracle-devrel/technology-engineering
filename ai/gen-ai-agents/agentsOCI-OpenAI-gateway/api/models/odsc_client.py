from oci.config import get_config_value_or_default, validate_config
from oci.signer import Signer
from oci.util import get_signer_from_authentication_type, AUTHENTICATION_TYPE_FIELD_NAME
import requests
import json
import sseclient


class DataScienceAiInferenceClient(object):
    def __init__(self, config, **kwargs):
        validate_config(config, signer=kwargs.get('signer'))
        if 'signer' in kwargs:
            self.signer = kwargs['signer']

        elif AUTHENTICATION_TYPE_FIELD_NAME in config:
            self.signer = get_signer_from_authentication_type(config)

        else:
            self.signer = Signer(
                tenancy=config["tenancy"],
                user=config["user"],
                fingerprint=config["fingerprint"],
                private_key_file_location=config.get("key_file"),
                pass_phrase=get_config_value_or_default(config, "pass_phrase"),
                private_key_content=config.get("key_content")
            )
        self.session = requests.Session()

    class ChatDetails(object):
        def __init__(self, messages, **kwargs):
            self.model = "odsc-llm"
            self.messages = messages
            self.max_tokens = kwargs.get("max_tokens", 1024)
            self.temperature = kwargs.get("temperature", 0)
            self.top_p = kwargs.get("top_p", 0.75)
            self.stream = kwargs.get("stream", True)
            self.frequency_penalty = kwargs.get("frequency_penalty", 0)
            self.presence_penalty = kwargs.get("frequency_penalty", 0)

    def chat(self, endpoint, chat_details, **kwargs):
        is_stream = chat_details["stream"]

        return self.call_api(
            endpoint=endpoint,
            is_stream=is_stream,
            chat_details=chat_details)

    def call_api(self, endpoint, is_stream, chat_details, **kwargs):
        if is_stream:
            header_params = {'Content-Type': 'application/json',
                             'enable-streaming': 'true',
                             'Accept': 'text/event-stream'}
        else:
            header_params = {'Content-Type': 'application/json',
                             'enable-streaming': 'false',
                             'Accept': 'application/json'}

        response = self.session.request(
            method='POST',
            url=endpoint,
            json=chat_details,
            auth=self.signer,
            stream=is_stream,
            headers=header_params)
        if is_stream:
            client = sseclient.SSEClient(response)
            return client
        else:
            return json.loads(response.text)
