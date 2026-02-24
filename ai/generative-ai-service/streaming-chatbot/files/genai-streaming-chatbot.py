import json
import oci
from oci.generative_ai_inference import GenerativeAiInferenceClient
from oci.generative_ai_inference.models import OnDemandServingMode, ChatDetails, CohereChatRequest

compartment_id = "ocid1.compartment.oc1..XXXXXXXXXXXXXXXXXXXXX"
model_id = "ocid1.generativeaimodel.oc1.XXXXXXXXXXXXXXXXXXXXXX"
endpoint = "https://inference.generativeai.XXXXXXXXXXXXXXXXXXX"

CONFIG_PROFILE = "DEFAULT"

config = oci.config.from_file('~/.oci/config', CONFIG_PROFILE)

def get_llm_response(prompt):
    client = GenerativeAiInferenceClient(
        config=config,
        service_endpoint=endpoint,
        retry_strategy=oci.retry.NoneRetryStrategy(),
        timeout=(10, 240)
    )

    chat_request = CohereChatRequest(
        message=prompt,
        max_tokens=600,
        temperature=0.5,
        frequency_penalty=0,
        top_p=0.75,
        top_k=0,
        is_stream=True  # Enable streaming
    )

    chat_detail = ChatDetails(
        serving_mode=OnDemandServingMode(model_id=model_id),
        chat_request=chat_request,
        compartment_id=compartment_id
    )

    try:
        response = client.chat(chat_detail)

        buffer = ""
        for event in response.data.events():
            if not event.data:
                continue

            buffer += event.data.strip()
            try:
                event_json = json.loads(buffer)
                buffer = ""  # clear buffer if parse succeeded
            except json.JSONDecodeError:
                # wait for more chunks
                continue

            text_chunk = event_json.get("text")
            if text_chunk:
                yield text_chunk

    except Exception as e:
        yield f"\n[Error during streaming: {e}]\n"

def main():
    print("OCI GenAI chatbot. Type 'exit' to quit.")
    while True:
        user_input = input("You: ")
        if user_input.strip().lower() == 'exit':
            print("Goodbye!")
            break
        print("Assistant: ", end="", flush=True)
        for token in get_llm_response(user_input):
            print(token, end="", flush=True)
        print()

if __name__ == "__main__":
    main()