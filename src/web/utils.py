import json
import logging
import uuid
import requests
import time
from datetime import datetime # Added import
from azure.eventhub import EventHubProducerClient, EventData
from azure.cosmos import CosmosClient, PartitionKey
from azure.identity import DefaultAzureCredential
from config import get_settings
from dotenv import load_dotenv
import os
from azure.ai.projects import AIProjectClient
from azure.ai.agents.models import MessageRole

load_dotenv(override=True)

# Initialize Cosmos client
endpoint = os.getenv("COSMOS_ENDPOINT")
key = os.getenv("COSMOS_KEY")
client = CosmosClient(endpoint, key)

database_name = os.getenv("COSMOS_DATABASE")
container_name = os.getenv("COSMOS_CONTAINER")


def get_user_chats(user_id='nikwieci'):
    """
    Retrieves user-specific chat thread entries from Cosmos DB.
    Filters by user_id.
    """
    try:
        # Use the global client, database_name, and container_name
        container = client.get_database_client(database_name).get_container_client(container_name)
        
        # Query for items matching the user_id
        # Using parameters in the query for security and correctness
        query = "SELECT * FROM c WHERE c.user_id = @user_id"
        parameters = [
            {"name": "@user_id", "value": user_id}
        ]
        
        items = list(container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=True # Keep this if user_id is not the partition key
        ))
        
        logging.info(f"Retrieved {len(items)} chat threads for user_id: {user_id}")
        return items
        
    except Exception as e:
        logging.exception(f"Failed to retrieve user chats from Cosmos DB for user_id {user_id}: {e}")
        raise # Or return empty list: return []


def get_chat_title(conversation_text: str, gpt_model: str = 'gpt-4.1') -> str:
    """
    Generates a 5-word title for a given conversation text.

    Args:
        conversation_text (str): The text of the conversation.
        gpt_model (str): The GPT model to use for summarization.

    Returns:
        str: A 5-word title for the conversation.
    """

    # Define the prompt for generating the chat title
    title_generation_prompt = """Based on the following conversation, generate a concise 5-word title.
    The title should capture the main topic or essence of the discussion.
    Provide only the 5-word title and nothing else."""

    messages = [
        {"role": "system", "content": title_generation_prompt},
        {"role": "user", "content": conversation_text}
    ]

    api_base = os.environ.get('AOAI_ENDPOINT')
    api_key = os.environ.get('AOAI_KEY')
    deployment_name = gpt_model

    if not api_base or not api_key:
        logging.error("Azure OpenAI endpoint (AOAI_ENDPOINT) or key (AOAI_KEY) is not set in environment variables.")
        return "Error: Missing API configuration."

    base_url = f"{api_base}openai/deployments/{deployment_name}"
    headers = {
        "Content-Type": "application/json",
        "api-key": api_key
    }
    # Ensure the API version is current or appropriate for your deployment
    endpoint_url = f"{base_url}/chat/completions?api-version=2024-02-01"  # Using a common recent API version

    data = {
        "messages": messages,
        "temperature": 0.2,  # Adjusted for more deterministic output for a title
        "max_tokens": 20,  # Max tokens for a 5-word title should be small
    }

    processed = False
    out_str = 'Error generating title.'  # Default error message

    retries = 3
    for attempt in range(retries):
        try:
            response = requests.post(endpoint_url, headers=headers, data=json.dumps(data), timeout=30)
            if response.status_code == 429:
                logging.warning(f"Rate limit exceeded. Retrying in {5 * (attempt + 1)} seconds...")
                time.sleep(5 * (attempt + 1))
                continue
            response.raise_for_status()  # Raises an HTTPError for bad responses (4XX or 5XX)

            resp_json = response.json()
            if resp_json.get('choices') and resp_json['choices'][0].get('message') and resp_json['choices'][0]['message'].get('content'):
                out_str = resp_json['choices'][0]['message']['content'].strip()
                processed = True
                break
            else:
                logging.error(f"Unexpected response structure: {resp_json}")
                out_str = "Error: Unexpected API response structure."

        except requests.exceptions.RequestException as e:
            logging.exception(f"Request failed on attempt {attempt + 1}: {e}")
            if attempt == retries - 1:  # Last attempt
                out_str = f"Error: API request failed after {retries} attempts."
        except Exception as e:  # Catch other potential errors like JSON parsing
            logging.exception(f"An unexpected error occurred on attempt {attempt + 1}: {e}")
            if attempt == retries - 1:
                out_str = "Error: An unexpected error occurred."

    return out_str


def add_thread_entry_to_cosmos(agent_id: str, thread_id: str, foundry_endpoint: str, user_id: str, chat_type: str):
    """
    Adds a new thread entry to Cosmos DB, including a timestamp.

    Args:
        agent_id: The ID of the agent.
        thread_id: The ID of the thread.
        foundry_endpoint: The Foundry endpoint.
        user_id: The ID of the user.
        chat_type: The type of chat (SYSTEM or USER).
    """
    try:
        container = client.get_database_client(database_name).get_container_client(container_name)
        current_timestamp = datetime.utcnow().isoformat() # Added timestamp
        entry = {
            "id": thread_id,
            "agent_id": agent_id,
            "thread_id": thread_id,
            "foundry_endpoint": foundry_endpoint,
            "user_id": user_id,
            "chat_type": chat_type,
            "timestamp": current_timestamp  # Added timestamp
            # Add other relevant fields as necessary
        }
        print(entry)
        container.create_item(body=entry)
        logging.info(f"Successfully added entry with id {thread_id} to Cosmos DB.")
        return entry
    except Exception as e:
        logging.exception(f"Failed to add thread entry to Cosmos DB: {e}")
        raise


def update_cosmos_record(item_id: str, user_id: str, **kwargs):
    """
    Updates an existing record in Cosmos DB.
    Assumes 'user_id' is the partition key.

    Args:
        item_id: The ID of the item to update.
        user_id: The user ID (partition key).
        **kwargs: Key-value pairs to update in the record.
    """
    try:
        container = client.get_database_client(database_name).get_container_client(container_name)

        # Read the existing item
        item_to_update = container.read_item(item=item_id, partition_key=user_id)

        # Update fields
        for key, value in kwargs.items():
            item_to_update[key] = value

        # Replace the item
        container.replace_item(item=item_id, body=item_to_update)
        logging.info(f"Successfully updated record with id {item_id} in Cosmos DB.")
        return item_to_update
    except Exception as e:
        logging.exception(f"Failed to update record {item_id} in Cosmos DB: {e}")
        raise


def get_system_chats(user_id):
    return [
        {
            'chat_title': 'Red Flag 19374',
            'thread_id': '789',
            'urgency': 'high',
            'messages': [
                {'role': 'assistant', 'content': 'System maintenance is scheduled at 10 PM.'},
                {'role': 'assistant', 'content': 'Maintenance completed successfully.'}
            ]
        },
        {
            'chat_title': 'Red Flag 83004',
            'thread_id': '110',
            'urgency': 'med',
            'messages': [
                {'role': 'assistant', 'content': 'Server CPU usage is at 85%.'},
                {'role': 'assistant', 'content': 'Auto‑scaling initiated to handle load.'}
            ]
        }
    ]


logger = logging.getLogger(__name__)


def push_to_event_hub(client_id: str):
    """
    Sends a single message to the specified Azure Event Hub.

    :param message: The message payload to send (string).
    :param connection_str: The full Event Hubs namespace connection string.
    :param eventhub_name: The name of the Event Hub.
    """
    try:
        # Create a producer client to send messages to the event hub.
        producer = EventHubProducerClient(
            fully_qualified_namespace=get_settings().event_hub_fully_qualified_namespace,
            eventhub_name=get_settings().event_hub_name,
            credential=DefaultAzureCredential()
        )

        # Use the client as a context manager to ensure clean-up.
        with producer:
            # Create a batch. You can add multiple events to the batch if desired.
            event_batch = producer.create_batch()

            with open('sample_red_flag.json', 'r', encoding='utf-8') as f:
                message = json.loads(f.read())

            message['client_id'] = client_id

            # Add your message as an EventData. You can also send bytes or JSON strings.
            event_batch.add(EventData(json.dumps(message)))

            logger.debug(event_batch)

            # Send the batch of events to the event hub.
            producer.send_batch(event_batch)

            return message
    except Exception as e:
        logger.exception("Failed to send message to Event Hub: %s", e)
        raise

def get_thread(thread_id, foundry_endpoint):
    """
    Retrieves messages from a specific thread using the AIProjectClient.

    Args:
        thread_id (str): The ID of the thread to retrieve messages from.
        foundry_endpoint (str): The endpoint of the Foundry project.

    Returns:
        list: A list of formatted messages, where each message is a dictionary
              with 'role' (user or assistant) and 'content'.
    """
    # Initialize the AIProjectClient with the provided endpoint and default credentials
    project_client = AIProjectClient(
            endpoint=foundry_endpoint,
            credential=DefaultAzureCredential(),
        )
    # List messages in the specified thread, ordered chronologically (ascending)
    messages = project_client.agents.messages.list(thread_id, order='asc')
    
    formatted_messages = []
    # Iterate through the retrieved messages
    for message in messages:
        # Check the role of the message
        if message.role == MessageRole.USER:
            # Format user messages
            formatted_messages.append({'role': 'user', 'content': message.content[0].text.value})
        else:
            # Format assistant messages (or any other role)
            formatted_messages.append({'role': 'assistant', 'content': message.content[0].text.value})
    # Return the list of formatted messages
    return formatted_messages