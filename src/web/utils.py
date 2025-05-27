import logging
from azure.eventhub import EventHubProducerClient, EventData
from azure.cosmos import CosmosClient, PartitionKey
from azure.identity import DefaultAzureCredential
from config import get_settings

# Initialize Cosmos client
# endpoint = os.getenv("COSMOS_ENDPOINT")

# client = CosmosClient(endpoint, DefaultAzureCredential())

# database_name = os.getenv("COSMOS_DATABASE")
# container_name = os.getenv("COSMOS_CONTAINER")


def get_user_chats(user_id='nikwieci'):
    return []
    container = client.get_database_client(database_name).get_container_client(container_name)
    query = f"""SELECT * FROM c WHERE c.userid = '{user_id}' AND c.source = 'user'"""
    items = container.query_items(
        query=query,
        enable_cross_partition_query=True
    )
    chats = []
    for item in items:
        chat = {
            'chat_title': item['title'],
            'thread_id': item['thread_id'],
            'urgency': '',
            'messages': item['conversation'],
            'user_id': item['userid'],
        }
        chats.append(chat)

    logging.info(chats)

    return chats


def get_system_chats(user_id):
    return [
        {
            'chat_title': 'Red Flag 19374',
            'thread_id': '789',
            'urgency': 'high',
            'messages': [
                {'role': 'assistant', 'content': 'System maintenance is scheduled at 10 PM.'},
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


def push_to_event_hub():
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
                message = f.read()

            # Add your message as an EventData. You can also send bytes or JSON strings.
            event_batch.add(EventData(message))

            logger.debug(event_batch)

            # Send the batch of events to the event hub.
            producer.send_batch(event_batch)

            return message
    except Exception as e:
        logger.exception("Failed to send message to Event Hub: %s", e)
        raise
