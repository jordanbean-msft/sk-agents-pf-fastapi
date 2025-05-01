def get_user_chats(user_id):
    return [
        {
            'chat_title': 'Chat A',
            'thread_id': '123',
            'urgency': 'low',
            'messages': [
                {'role': 'user', 'content': 'Hello, how can I reset my password?'},
                {'role': 'assistant', 'content': 'To reset your password, go to the account settings and click "Reset Password".'},
                {'role': 'user', 'content': 'I don’t see the settings option for my account.'},
                {'role': 'assistant', 'content': 'Make sure you’re logged in. If the issue persists, contact support.'}
            ]
        },
        {
            'chat_title': 'Chat B',
            'thread_id': '456',
            'urgency': 'low',
            'messages': [
                {'role': 'user', 'content': 'Is the monthly report ready?'},
                {'role': 'assistant', 'content': 'The report will be available by end of day today.'},
                {'role': 'user', 'content': 'Great, thanks!'}
            ]
        }
    ]

def get_system_chats(user_id):
    return [
        {
            'chat_title': 'System A',
            'thread_id': '789',
            'urgency': 'high',
            'messages': [
                {'role': 'assistant', 'content': 'System maintenance is scheduled at 10 PM.'},
                {'role': 'assistant', 'content': 'Maintenance completed successfully.'}
            ]
        },
        {
            'chat_title': 'System B',
            'thread_id': '110',
            'urgency': 'med',
            'messages': [
                {'role': 'assistant', 'content': 'Server CPU usage is at 85%.'},
                {'role': 'assistant', 'content': 'Auto‑scaling initiated to handle load.'}
            ]
        }
    ]

from azure.eventhub import EventHubProducerClient, EventData  
import logging  
  
logging.basicConfig(level=logging.INFO)  
logger = logging.getLogger(__name__)  

from dotenv import load_dotenv
import os
load_dotenv('.env', override=True)  # Load environment variables from .env file
  
def push_to_event_hub() -> None:  
    """  
    Sends a single message to the specified Azure Event Hub.  
  
    :param message: The message payload to send (string).  
    :param connection_str: The full Event Hubs namespace connection string.  
    :param eventhub_name: The name of the Event Hub.  
    """  
    try:  
        # Create a producer client to send messages to the event hub.  
        producer = EventHubProducerClient.from_connection_string(  
            conn_str=os.getenv("EVENT_HUB_CONN_STR"),  
            eventhub_name=os.getenv("EVENT_HUB_NAME")  
        )  
  
        # Use the client as a context manager to ensure clean-up.  
        with producer:  
            # Create a batch. You can add multiple events to the batch if desired.  
            event_batch = producer.create_batch()  

            with open('sample_red_flag.json', 'r') as f:
                message = f.read()
  
            # Add your message as an EventData. You can also send bytes or JSON strings.  
            event_batch.add(EventData(message))  

            print(event_batch)
  
            # Send the batch of events to the event hub.  
            producer.send_batch(event_batch) 
             
            return message
    except Exception as e:  
        logger.exception("Failed to send message to Event Hub: %s", e)  
        raise  