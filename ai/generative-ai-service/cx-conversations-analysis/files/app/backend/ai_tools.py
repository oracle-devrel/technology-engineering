import json
import os
from time import sleep

import oci
from oci.generative_ai_inference.models import (
    BaseChatRequest,
    ChatDetails,
    GenericChatRequest,
    OnDemandServingMode,
    SystemMessage,
    TextContent,
    UserMessage,
)


class SpeechPipeline:
    "A class to transcribe the audio from a Video file"

    def __init__(self, config):
        oci_config = oci.config.from_file(
            config.CONFIG_FILE_PATH, profile_name=config.PROFILE_NAME
        )
        self.client = oci.ai_speech.AIServiceSpeechClient(oci_config)
        self.object_client = oci.object_storage.ObjectStorageClient(oci_config)
        self.config = config

    def upload_file_to_object_storage(self, file_path, object_name):
        with open(file_path, "rb") as f:
            response = self.object_client.put_object(
                namespace_name=self.config.BUCKET_NAMESPACE,
                bucket_name=self.config.BUCKET_NAME,
                object_name=object_name,
                put_object_body=f,
            )
        print("Upload complete to bucket complete.")
        return response

    def get_transcription(
        self,
        audio_file,
        model_type,
        whisper_prompt=None,
        diarization=True,
        number_of_speakers=None,
    ):
        object_name = os.path.join(
            self.config.BUCKET_FILE_PREFIX, os.path.basename(audio_file)
        )
        _ = self.upload_file_to_object_storage(audio_file, object_name)

        # Getting video file input location
        object_location_1 = oci.ai_speech.models.ObjectLocation(
            namespace_name=self.config.BUCKET_NAMESPACE,
            bucket_name=self.config.BUCKET_NAME,
            object_names=[object_name],
        )
        input_location = oci.ai_speech.models.ObjectListInlineInputLocation(
            location_type="OBJECT_LIST_INLINE_INPUT_LOCATION",
            object_locations=[object_location_1],
        )

        # Creating output location
        output_location = oci.ai_speech.models.OutputLocation(
            namespace_name=self.config.BUCKET_NAMESPACE,
            bucket_name=self.config.BUCKET_NAME,
            prefix=self.config.SPEECH_BUCKET_OUTPUT_PREFIX,
        )

        ## Speech Model and configuration:
        model_config = oci.ai_speech.models.TranscriptionModelDetails()

        if model_type == "Oracle":
            model_config.model_type = "ORACLE"
            model_config.domain = "GENERIC"
            model_config.language_code = "en-US"
        else:
            model_config.model_type = "WHISPER_LARGE_V3T"
            model_config.domain = "GENERIC"
            model_config.language_code = "en"

        transcription_settings = oci.ai_speech.models.TranscriptionSettings(
            diarization=oci.ai_speech.models.Diarization(
                is_diarization_enabled=diarization,
                number_of_speakers=number_of_speakers,
            )
        )
        if model_type == "Whisper" and whisper_prompt is not None:
            transcription_settings.additional_settings = {
                "whisperPrompt": whisper_prompt  # Only valid for Whisper models.
            }

        model_config.transcription_settings = transcription_settings

        ## Create transcription job
        transcription_job = self.client.create_transcription_job(
            create_transcription_job_details=oci.ai_speech.models.CreateTranscriptionJobDetails(
                compartment_id=self.config.COMPARTMENT_ID,
                input_location=input_location,
                output_location=output_location,
                model_details=model_config,
            )
        )
        job_id = transcription_job.data.id
        seconds = 0
        while (
            transcription_job.data.lifecycle_state == "IN_PROGRESS"
            or transcription_job.data.lifecycle_state == "ACCEPTED"
        ):
            print(
                f"Job {job_id} is IN_PROGRESS for {str(seconds)} seconds, progress: {transcription_job.data.percent_complete}"
            )
            sleep(2)
            seconds += 2
            transcription_job = self.client.get_transcription_job(
                transcription_job_id=job_id
            )

        print(f"Job {job_id} is in {transcription_job.data.lifecycle_state} state.")
        if transcription_job.data.lifecycle_state == "FAILED":
            return f"Transcription job {job_id} failed."

        # Getting response from object storage
        list_response = self.object_client.list_objects(
            namespace_name=transcription_job.data.output_location.namespace_name,
            bucket_name=transcription_job.data.output_location.bucket_name,
            prefix=transcription_job.data.output_location.prefix,
        )
        output_object_name = list_response.data.objects[0].name
        transcription_response = self.object_client.get_object(
            output_location.namespace_name,
            output_location.bucket_name,
            output_object_name,
        )
        return transcription_response


class GenAIPipeline:
    def __init__(self, config):
        oci_config = oci.config.from_file(
            config.CONFIG_FILE_PATH, profile_name=config.PROFILE_NAME
        )
        self.generative_ai_inference_client = (
            oci.generative_ai_inference.GenerativeAiInferenceClient(
                config=oci_config,
                service_endpoint=config.ENDPOINT,
                retry_strategy=oci.retry.NoneRetryStrategy(),
                timeout=(10, 240),
            )
        )
        self.config = config

    def get_chat_response(self, system_prompt, user_prompt, model_id):
        # ----- 1. Build messages with explicit roles (SYSTEM + USER) -----
        system_msg = SystemMessage(content=[TextContent(text=str(system_prompt))])
        user_msg = UserMessage(content=[TextContent(text=str(user_prompt))])
        messages = [system_msg, user_msg]

        # ----- 2. Configure the generic chat request to highlight model features -----
        chat_request = GenericChatRequest(
            api_format=BaseChatRequest.API_FORMAT_GENERIC,
            messages=messages,
            # generation controls
            max_tokens=128000,
            temperature=0.5,
            top_p=0.8,
            top_k=-1,
            frequency_penalty=0.0,
            presence_penalty=0.0,
        )

        # ----- 3. Wrap in ChatDetails with on-demand serving mode -----
        chat_detail = ChatDetails(
            compartment_id=self.config.COMPARTMENT_ID,
            serving_mode=OnDemandServingMode(model_id=model_id),
            chat_request=chat_request,
        )

        # ----- 4. Call the service and extract the assistant text -----
        response = self.generative_ai_inference_client.chat(chat_detail)

        chat_response = response.data.chat_response
        first_choice = chat_response.choices[0]
        first_content = first_choice.message.content[0]
        json_text = first_content.text.strip()
        json_parsed = json.loads(json_text)

        return json_parsed


def post_process_trans(transcription_response, diarization=True):
    object_content_bytes = transcription_response.data.content  # this is in bytes
    object_content_str = object_content_bytes.decode("utf-8")

    transcription_json = json.loads(object_content_str)
    if diarization:
        speakers_list = arrange_text_by_speaker(
            transcription_json["transcriptions"][0]["tokens"]
        )
    else:
        speakers_list = []
    transcriptions = transcription_json.get("transcriptions", [])
    text_trans = "\n".join([trans["transcription"] for trans in transcriptions])
    return text_trans, speakers_list


def arrange_text_by_speaker(transcription_tokens):
    speakers_list = []
    current_speaker = transcription_tokens[0]["speakerIndex"]
    current_dict = {"speaker_id": current_speaker, "speaker_text": ""}
    for tok in transcription_tokens:
        tok_speaker = tok["speakerIndex"]
        tok_text = tok["token"]
        if tok_speaker == current_speaker:
            current_dict["speaker_text"] = current_dict["speaker_text"] + " " + tok_text
        else:
            # change of speaker
            speakers_list.append(current_dict)
            current_speaker = tok_speaker
            current_dict = {"speaker_id": tok_speaker, "speaker_text": tok_text}

    speakers_list.append(current_dict)
    return speakers_list
