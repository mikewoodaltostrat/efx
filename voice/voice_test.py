import asyncio
import uuid
import logging
import argparse
import sys
from typing import List
from google.cloud import dialogflowcx_v3 as dialogflow
from google.cloud.dialogflowcx_v3 import SessionsAsyncClient as SessionsClient
from google.api_core.exceptions import ResourceExhausted

async def send_single_request(
    client: SessionsClient,
    session_path: str,
    text_to_send: str,
    request_num: int,
    voice_tag: str,
    semaphore: asyncio.Semaphore,
    shutdown_event: asyncio.Event
):
    """
    Defines a single asynchronous task that checks a shutdown event,
    acquires a semaphore, and sends one intent request.
    """
    if shutdown_event.is_set():
        logging.warning(f"Request #{request_num}: Shutdown signaled, cancelling task.")
        return

    async with semaphore:
        if shutdown_event.is_set():
            logging.warning(f"Request #{request_num}: Shutdown signaled, cancelling task.")
            return

        logging.info(f"Request #{request_num}: Semaphore acquired, sending '{text_to_send}'...")
        
        # 1. Read the audio file into memory
        AUDIO_FILE_PATH="./test_16khz.wav"
        with open(AUDIO_FILE_PATH, "rb") as audio_file:
            input_audio = audio_file.read()

        # 2. Configure the input audio format
        audio_config = dialogflow.InputAudioConfig(
            audio_encoding=dialogflow.AudioEncoding.AUDIO_ENCODING_LINEAR_16,
            sample_rate_hertz=16000, # Match your 16kHz file
            model='telephony_short'  # A great model for short, 16kHz commands
        )

        # 3. Create the audio query input
        query_input = dialogflow.QueryInput(
            audio=dialogflow.AudioInput(config=audio_config, audio=input_audio),
            language_code="en-US",
        )

        # 4. Configure the desired output voice (e.g., Neural2)
        # The voice name would change based on whether you're testing standard or neural.
        synthesize_speech_config = dialogflow.SynthesizeSpeechConfig(
            voice=dialogflow.VoiceSelectionParams(name=voice_tag)
        )

        output_audio_config = dialogflow.OutputAudioConfig(
            synthesize_speech_config=synthesize_speech_config
        )

        # 5. Build the final request with the output audio config
        request = dialogflow.DetectIntentRequest(
            session=session_path,
            query_input=query_input,
            output_audio_config=output_audio_config, # Add this line
        )

        try:
            response = await client.detect_intent(request=request)
            # --- CHANGE #2: Check the match type to determine success ---
            # A successful response is one where an intent was actually matched.
            logging.info(f"STT Transcript: '{response.query_result.transcript}'")

            match_type = response.query_result.match.match_type
            if match_type != dialogflow.Match.MatchType.NO_MATCH:
                intent_name = response.query_result.match.intent.display_name
                logging.info(f"Request #{request_num} --> SUCCESS (Intent Matched: {intent_name})")
                logging.info(f"session_path={session_path}")
            else:
                logging.error(f"Request #{request_num} --> FAILED (No Match)")

        except ResourceExhausted as exp:
            logging.error(f"Request #{request_num} FAILED (Quota Exceeded). Signaling shutdown...")
            logging.error(exp)
            shutdown_event.set()
        except Exception as e:
            logging.error(f"Request #{request_num} FAILED (API Error): {e}")


async def main(args):
    """Sets up clients and configuration, then creates and runs all concurrent tasks."""
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()]
    )

    client_options = {"api_endpoint": f"{args.location}-dialogflow.googleapis.com"}
    client = SessionsClient(client_options=client_options)

    session_ids = [str(uuid.uuid4()), str(uuid.uuid4())]
    session_paths = [
        client.session_path(
            project=args.project_ids[0], location=args.location, agent=args.agent_ids[0], session=session_ids[0]
        ),
        client.session_path(
            project=args.project_ids[1], location=args.location, agent=args.agent_ids[1], session=session_ids[1]
        )
    ]
    
    shutdown_event = asyncio.Event()
    semaphore = asyncio.Semaphore(args.concurrency_limit)
    
    logging.info(f"Preparing {args.num_requests} requests with a concurrency limit of {args.concurrency_limit}.")
    
    tasks = []
    text_to_send = "test"
    
    for i in range(args.num_requests):
        index = args.voice
        voice_tag = args.voice_tag[index]
        task = asyncio.create_task(
            send_single_request(
                client=client,
                session_path=session_paths[index],
                text_to_send=text_to_send,
                request_num=i + 1,
                voice_tag=voice_tag,
                semaphore=semaphore,
                shutdown_event=shutdown_event
            )
        )
        tasks.append(task)
        
    await asyncio.gather(*tasks)
    logging.info("All concurrent requests have been processed.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run a concurrent load test against Dialogflow CX agents.")
    
    parser.add_argument(
        '--project-ids',
        nargs=2,
        default=['efx-dialogflow-standard', 'efx-dialogflow-neural2'],
        help="A list of two Google Cloud project IDs (standard first, neural2 second)."
    )
    parser.add_argument(
        '--voice-tag',
        nargs=2,
        default=['en-US-Standard-A', 'en-US-Neural2-A'],
        help="A list of two Google Cloud voice tags (standard first, neural2 second)."
    )
    parser.add_argument(
        '--agent-ids',
        nargs=2,
        default=['663759f3-d235-481d-8b5f-0e5f3fa8dd68', '627f6101-e1e6-4871-92dd-e1be42b51afe'],
        help="A list of two Dialogflow agent IDs (standard first, neural2 second)."
    )
    parser.add_argument(
        '--location',
        type=str,
        default='us-central1',
        help="The GCP region where the agents are hosted."
    )
    parser.add_argument(
        '--num-requests',
        type=int,
        default=2,
        help="The total number of requests to send."
    )
    parser.add_argument(
        '--concurrency-limit',
        type=int,
        default=10,
        help="Maximum number of concurrent requests."
    )
    parser.add_argument(
        "--voice",
        type=int,
        choices=[0, 1],  # Defines the allowed values for --voice
        help="Specify the voice to use (0 or 1)."
)

    args = parser.parse_args()
    
    asyncio.run(main(args))