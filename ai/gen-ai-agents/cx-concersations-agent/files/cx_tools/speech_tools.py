import json
import os
from time import sleep

import oci
from langchain_core.tools import tool

from .config import OCIConfig


# ── Low-level pipeline (unchanged from original) ──────────────────────────────

class SpeechPipeline:

    def __init__(self, config: OCIConfig):
        oci_config = oci.config.from_file(
            config.CONFIG_FILE_PATH, profile_name=config.PROFILE_NAME
        )
        self.client = oci.ai_speech.AIServiceSpeechClient(oci_config)
        self.object_client = oci.object_storage.ObjectStorageClient(oci_config)
        self.config = config

    def upload_file_to_object_storage(self, file_path: str, object_name: str):
        with open(file_path, "rb") as f:
            response = self.object_client.put_object(
                namespace_name=self.config.BUCKET_NAMESPACE,
                bucket_name=self.config.BUCKET_NAME,
                object_name=object_name,
                put_object_body=f,
            )
        print("Upload to bucket complete.")
        return response

    def get_transcription(
        self,
        audio_file: str,
        model_type: str,
        whisper_prompt: str | None = None,
        diarization: bool = True,
        number_of_speakers: int | None = None,
    ):
        object_name = os.path.join(
            self.config.BUCKET_FILE_PREFIX, os.path.basename(audio_file)
        )
        self.upload_file_to_object_storage(audio_file, object_name)

        object_location = oci.ai_speech.models.ObjectLocation(
            namespace_name=self.config.BUCKET_NAMESPACE,
            bucket_name=self.config.BUCKET_NAME,
            object_names=[object_name],
        )
        input_location = oci.ai_speech.models.ObjectListInlineInputLocation(
            location_type="OBJECT_LIST_INLINE_INPUT_LOCATION",
            object_locations=[object_location],
        )
        output_location = oci.ai_speech.models.OutputLocation(
            namespace_name=self.config.BUCKET_NAMESPACE,
            bucket_name=self.config.BUCKET_NAME,
            prefix=self.config.SPEECH_BUCKET_OUTPUT_PREFIX,
        )

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
                "whisperPrompt": whisper_prompt
            }
        model_config.transcription_settings = transcription_settings

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
        while transcription_job.data.lifecycle_state in ("IN_PROGRESS", "ACCEPTED"):
            print(
                f"Job {job_id} IN_PROGRESS for {seconds}s, "
                f"progress: {transcription_job.data.percent_complete}"
            )
            sleep(2)
            seconds += 2
            transcription_job = self.client.get_transcription_job(
                transcription_job_id=job_id
            )

        print(f"Job {job_id} finished: {transcription_job.data.lifecycle_state}")
        if transcription_job.data.lifecycle_state == "FAILED":
            return f"Transcription job {job_id} failed."

        list_response = self.object_client.list_objects(
            namespace_name=transcription_job.data.output_location.namespace_name,
            bucket_name=transcription_job.data.output_location.bucket_name,
            prefix=transcription_job.data.output_location.prefix,
        )
        output_object_name = list_response.data.objects[0].name
        return self.object_client.get_object(
            output_location.namespace_name,
            output_location.bucket_name,
            output_object_name,
        )


# ── Post-processing helpers (unchanged) ───────────────────────────────────────

def post_process_trans(transcription_response, diarization: bool = True):
    content = transcription_response.data.content.decode("utf-8")
    transcription_json = json.loads(content)

    speakers_list = (
        _arrange_text_by_speaker(transcription_json["transcriptions"][0]["tokens"])
        if diarization
        else []
    )
    text_trans = "\n".join(
        t["transcription"] for t in transcription_json.get("transcriptions", [])
    )
    return text_trans, speakers_list


def _arrange_text_by_speaker(tokens: list) -> list:
    speakers_list = []
    current_speaker = tokens[0]["speakerIndex"]
    current_dict = {"speaker_id": current_speaker, "speaker_text": ""}

    for tok in tokens:
        if tok["speakerIndex"] == current_speaker:
            current_dict["speaker_text"] += " " + tok["token"]
        else:
            speakers_list.append(current_dict)
            current_speaker = tok["speakerIndex"]
            current_dict = {"speaker_id": current_speaker, "speaker_text": tok["token"]}

    speakers_list.append(current_dict)
    return speakers_list


# ── LangChain Tool factory ────────────────────────────────────────────────────

def build_transcription_tool(config: OCIConfig):
    pipeline = SpeechPipeline(config)

    @tool
    def transcribe_audio(input_json: str) -> str:
        params = json.loads(input_json)
        response = pipeline.get_transcription(
            audio_file=params["audio_file"],
            model_type=params.get("model_type", "Whisper"),
            diarization=params.get("diarization", True),
            number_of_speakers=params.get("number_of_speakers"),
        )
        if isinstance(response, str):          # job failed
            return json.dumps({"error": response})

        transcript, speakers = post_process_trans(
            response, diarization=params.get("diarization", True)
        )
        return json.dumps({"transcript": transcript, "speakers": speakers})

    return transcribe_audio
