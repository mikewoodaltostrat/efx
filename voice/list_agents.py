from google.cloud import dialogflowcx_v3 as dialogflow

def list_all_agents(project_id: str, location: str):
    """
    Lists all Dialogflow CX agents in a given project and location.

    Args:
        project_id: The Google Cloud project ID.
        location: The GCP region for the agents (e.g., 'us-central1').
    """
    # Create a client for the Agents API.
    # The client will automatically use the default credentials.
    client_options = {"api_endpoint": f"{location}-dialogflow.googleapis.com"}
    client = dialogflow.AgentsClient(client_options=client_options)

    # Initialize request argument(s)
    # The parent resource is the location where the agents are located.
    # The format is: "projects/<Project ID>/locations/<Location ID>"
    try:
        parent = f"projects/{project_id}/locations/{location}"
        print(f"parent={parent}")
        request = dialogflow.ListAgentsRequest(
            parent=parent,
        )
    except Exception as e:
        print(f"Error creating request: {e}")
        return 

    try:
        # Make the request
        page_result = client.list_agents(request=request)

    except Exception as e:
        print(f"Error making request: {e}")
        return


    # The parent resource is the location where the agents are located.
    # The format is: "projects/<Project ID>/locations/<Location ID>"

    # Call the API to list the agents.
    # This returns a Pager object that you can iterate over.
    try:
        agents_pager = client.list_agents(parent=parent)
    except Exception as e:
        print(f"Error listing agents: {e}")
        return

    # Iterate through the results and print agent details.
    agent_found = False
    for agent in agents_pager:
        agent_found = True
        print(f"{agent.name},{agent.display_name}")
        #print(f"-> Display Name: {agent.display_name}")
        #rint(f"   Resource Name: {agent.name}\n")

    if not agent_found:
        print("No agents found in this project and location.")


# --- Run the function with your details ---
if __name__ == "__main__":
    # Replace with your actual project ID and location
    GCP_PROJECT_ID = "efx-dialogflow-standard"
    GCP_LOCATION = "us-central1" # e.g., 'global', 'us-central1'
    
    list_all_agents(project_id=GCP_PROJECT_ID, location=GCP_LOCATION)