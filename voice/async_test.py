import asyncio
import uuid
import logging
import argparse
from typing import List
from google.cloud import dialogflowcx_v3 as dialogflow
# Use the ASYNC version of the Dialogflow CX client library
from google.cloud.dialogflowcx_v3 import SessionsAsyncClient as SessionsClient
from google.api_core.exceptions import ResourceExhausted

async def send_single_request(
    client: SessionsClient,
    session_path: str,
    text_to_send: str,
    request_num: int
):
    """
    Defines a single asynchronous task to send one intent request.
    This function is designed to be run concurrently.
    """
    query_input = dialogflow.QueryInput(
        text=dialogflow.TextInput(text=text_to_send),
        language_code="en-US",
    )
    request = dialogflow.DetectIntentRequest(
        session=session_path,
        query_input=query_input,
    )

    logging.info(f"Request #{request_num}: Sending '{text_to_send}'...")
    
    try:
        # Use 'await' for the asynchronous API call
        await client.detect_intent(request=request)
        
    except ResourceExhausted:
        logging.error(f"Request #{request_num} FAILED (Quota Exceeded)")
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

    # Set up a unique session for each of the two agents
    session_ids = [str(uuid.uuid4()), str(uuid.uuid4())]
    session_paths = [
        client.session_path(
            project=args.project_ids[0], location=args.location, agent=args.agent_ids[0], session=session_ids[0]
        ),
        client.session_path(
            project=args.project_ids[1], location=args.location, agent=args.agent_ids[1], session=session_ids[1]
        )
    ]
    
    logging.info(f"Preparing {args.num_requests} concurrent requests.")
    
    text_inputs = ["test", "test"]
    tasks = []
    
    # Create a list of all the tasks we want to run
    for i in range(args.num_requests):
        index = i % 2
        task = asyncio.create_task(
            send_single_request(
                client=client,
                session_path=session_paths[index],
                text_to_send=text_inputs[index],
                request_num=i + 1,
            )
        )
        tasks.append(task)
        
    # Run all the created tasks concurrently
    await asyncio.gather(*tasks)
    
    logging.info("All concurrent requests have been processed.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run a concurrent load test against Dialogflow CX agents.")
    
    # Arguments are the same as the previous script
    parser.add_argument('--project-ids', nargs=2, default=['efx-dialogflow-standard', 'efx-dialogflow-neural2'])
    parser.add_argument('--agent-ids', nargs=2, default=['663759f3-d235-481d-8b5f-0e5f3fa8dd68', '627f6101-e1e6-4871-92dd-e1be42b51afe'])
    parser.add_argument('--location', type=str, default='us-central1')
    parser.add_argument('--num-requests', type=int, default=200)

    args = parser.parse_args()
    
    # Use asyncio.run() to start the entire asynchronous process
    asyncio.run(main(args))