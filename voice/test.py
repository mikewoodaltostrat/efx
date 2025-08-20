import uuid
import logging
import mylib
from google.cloud import dialogflowcx_v3 as dialogflow
from google.api_core.exceptions import ResourceExhausted



def test_voice(num_requests):
    """Returns the result of detect intent with text as input.

    Using the same `session_id` between requests allows continuation
    of the conversation."""
    
    for i in range(num_requests):
        # Alternate between "standard" and "neural2" for each request
        text_input = "test"
        index = i % 2
        
        query_input = dialogflow.QueryInput(
            text=dialogflow.TextInput(text=text_input),
            language_code="en-US",
        )
        
        logger.info(f"count={i}, index={index}, project={project_ids[index]}, agent={agent_ids[index]}")
        request = dialogflow.DetectIntentRequest(
            session=session_paths[index],
            query_input=query_input,
        )
        
        try:
            response = client.detect_intent(request=request)
            
        except ResourceExhausted as e:
            # This specifically catches "429 Too Many Requests" errors, which are common for quotas.
            logger.error(f"Request #{i+1}: Sent '{text_input}' --> FAILED (Quota Exceeded)")
            logger.error(f"  └─ Details: {e.message}")
            break # Stop the script if we hit a quota limit
            
        except Exception as e:
            # This catches any other potential API error (authentication, network, etc.)
            logger.error(f"Request #{i+1}: Sent '{text_input}' --> FAILED (API Error)")
            logger.error(f"  └─ Details: {e}")
            break
            
# setup the logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()

# create the client
location = 'us-central1'
client_options = {"api_endpoint": f"{location}-dialogflow.googleapis.com"}
client = dialogflow.SessionsClient(client_options=client_options)

# look up the project_id to use for each intent to allocate the costs via project_id
project_ids = ['efx-dialogflow-standard','efx-dialogflow-neural2']
agent_ids = ['663759f3-d235-481d-8b5f-0e5f3fa8dd68','627f6101-e1e6-4871-92dd-e1be42b51afe']
session_ids = [uuid.uuid4(),uuid.uuid4()]
session_paths = [client.session_path(project=project_ids[0], location='us-central1', agent=agent_ids[0], session=session_ids[0]),
                 client.session_path(project=project_ids[1], location='us-central1', agent=agent_ids[1], session=session_ids[1])]

# Call the function with a sample user query
test_voice(num_requests=100000)
