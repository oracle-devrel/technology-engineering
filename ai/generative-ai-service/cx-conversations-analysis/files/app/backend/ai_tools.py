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
from oci.ai_language.models import (
    BatchDetectLanguageSentimentsDetails,
    TextDocument,
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
        # File uploaded to object storage successfully
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
            # Available Whisper models: WHISPER_MEDIUM, WHISPER_LARGE_V2 (requires service request)
            # Using WHISPER_MEDIUM as default since WHISPER_LARGE_V2 requires service request
            model_config.model_type = "WHISPER_MEDIUM"
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
            # Job progress is handled by UI progress indicators
            sleep(2)
            seconds += 2
            transcription_job = self.client.get_transcription_job(
                transcription_job_id=job_id
            )

        if transcription_job.data.lifecycle_state == "FAILED":
            # Extract error details if available
            error_message = f"Transcription job {job_id} failed."
            error_details = []
            
            # Check for lifecycle_details
            if hasattr(transcription_job.data, 'lifecycle_details') and transcription_job.data.lifecycle_details:
                error_details.append(f"Lifecycle details: {transcription_job.data.lifecycle_details}")
            
            # Check for error_message
            if hasattr(transcription_job.data, 'error_message') and transcription_job.data.error_message:
                error_details.append(f"Error message: {transcription_job.data.error_message}")
            
            if error_details:
                error_message += " " + " | ".join(error_details)
            
            return error_message

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

        # ----- 2. Configure the generic chat request with model-specific parameters -----
        # Model-specific parameter configuration based on provider
        is_grok_model = model_id.startswith("xai.")
        is_meta_model = model_id.startswith("meta.")
        
        # Base parameters for all models
        chat_request_params = {
            "api_format": BaseChatRequest.API_FORMAT_GENERIC,
            "messages": messages,
        }
        
        # Model-specific parameter configuration
        if is_grok_model:
            # Grok-specific parameters (based on reference implementation)
            # Grok doesn't support presence_penalty and frequency_penalty
            chat_request_params.update({
                "max_tokens": 128000,
                "temperature": 1.0,
                "top_p": 1.0,
                "top_k": 0,
            })
        elif is_meta_model:
            # Meta-specific parameters (based on Python reference implementation)
            # IMPORTANT: Meta models have a maximum of 4096 tokens for max_tokens
            chat_request_params.update({
                "max_tokens": 4000,  # Meta max is 4096, using 4000 for safety margin
                "temperature": 1.0,
                "top_p": 0.75,
                "frequency_penalty": 0.0,
                "presence_penalty": 0.0,
                # Note: top_k is not used in Meta reference code
            })
        else:
            # Default parameters for OpenAI and other models
            chat_request_params.update({
                "max_tokens": 128000,
                "temperature": 0.5,
                "top_p": 0.8,
                "top_k": -1,
                "frequency_penalty": 0.0,
                "presence_penalty": 0.0,
            })
        
        chat_request = GenericChatRequest(**chat_request_params)

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


class SentimentAnalysisPipeline:
    """
    A class to analyze sentiment using OCI Language Service.
    Converts OCI Language Service sentiment scores to a 1-10 scale.
    """

    def __init__(self, config):
        oci_config = oci.config.from_file(
            config.CONFIG_FILE_PATH, profile_name=config.PROFILE_NAME
        )
        self.ai_language_client = oci.ai_language.AIServiceLanguageClient(oci_config)
        self.config = config

    def analyze_sentiment(self, text: str, level: str = "SENTENCE") -> dict:
        """
        Analyze sentiment of text using OCI Language Service.
        
        Args:
            text: The text to analyze
            level: "SENTENCE" or "ASPECT" (default: "SENTENCE")
        
        Returns:
            dict with sentiment_score (1-10) and sentiment details
        """
        if not text or not text.strip():
            return {
                "sentiment_score": 5,  # Neutral default
                "sentiment": "neutral",
                "confidence": 0.0,
            }

        if not level or not isinstance(level, str):
            level = "SENTENCE"
        level = level.upper().strip()
        if level not in ["SENTENCE", "ASPECT"]:
            level = "SENTENCE"  # Default to SENTENCE if invalid

        # Convert to list as required by the API
        level_list = [level]

        # Prepare document for analysis
        document = TextDocument(key="doc1", text=text)
        details = BatchDetectLanguageSentimentsDetails(
            documents=[document]
        )

        # Call OCI Language Service
        try:
            response = self.ai_language_client.batch_detect_language_sentiments(
                batch_detect_language_sentiments_details=details,
                level=level_list,
            )

            if response.data and response.data.documents:
                doc_result = response.data.documents[0]
                document_sentiment = doc_result.document_sentiment.lower()
                document_scores = doc_result.document_scores

                # Convert OCI sentiment (positive/negative/neutral/mixed) to 1-10 scale
                sentiment_score = self._convert_to_scale_1_10(
                    document_sentiment, document_scores
                )

                return {
                    "sentiment_score": sentiment_score,
                    "sentiment": document_sentiment,
                    "confidence": max(
                        document_scores.get("positive", 0),
                        document_scores.get("negative", 0),
                        document_scores.get("neutral", 0),
                        document_scores.get("mixed", 0),
                    ),
                    "scores": document_scores,
                }
        except Exception as e:
            print(f"Error in sentiment analysis: {e}")
            # Return neutral default on error
            return {
                "sentiment_score": 5,
                "sentiment": "neutral",
                "confidence": 0.0,
            }

    def _convert_to_scale_1_10(
        self, sentiment: str, scores: dict
    ) -> int:
        """
        Convert OCI Language Service sentiment to 1-10 scale.
        
        OCI returns: positive, negative, neutral, mixed with confidence scores 0-1
        We convert to: 1 (very negative) to 10 (very positive), 5 (neutral)
        
        Formula:
        - If positive: 5 + (positive_score * 5) -> range 5-10
        - If negative: 5 - (negative_score * 4) -> range 1-5
        - If neutral: 5
        - If mixed: weighted average of positive and negative
        """
        positive_score = scores.get("positive", 0.0) or 0.0
        negative_score = scores.get("negative", 0.0) or 0.0
        neutral_score = scores.get("neutral", 0.0) or 0.0
        mixed_score = scores.get("mixed", 0.0) or 0.0

        if sentiment == "positive":
            # Map positive confidence (0-1) to 5-10 scale
            return int(round(5 + (positive_score * 5)))
        elif sentiment == "negative":
            # Map negative confidence (0-1) to 1-5 scale
            return int(round(5 - (negative_score * 4)))
        elif sentiment == "neutral":
            return 5
        elif sentiment == "mixed":
            # For mixed, calculate weighted average
            # Positive contributes to higher scores, negative to lower
            positive_contribution = positive_score * 5  # 0-5
            negative_contribution = negative_score * 4  # 0-4
            base_score = 5 + positive_contribution - negative_contribution
            return int(round(max(1, min(10, base_score))))
        else:
            # Default to neutral
            return 5


def post_process_trans(transcription_response, diarization=True):
    # Handle error case: if transcription_response is a string (error message)
    if isinstance(transcription_response, str):
        raise ValueError(f"Transcription failed: {transcription_response}")
    
    # Handle case where response doesn't have expected structure
    if not hasattr(transcription_response, 'data') or not hasattr(transcription_response.data, 'content'):
        raise ValueError(f"Invalid transcription response format: {type(transcription_response)}")
    
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
