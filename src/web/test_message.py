import asyncio
import websockets
import json

async def main():
    uri = "ws://localhost:6789"
    msg = {  
        'chat_title': 'Alert 24570',  
        'thread_id': '456',  
        'urgency': 'medium',  
        'messages': [  
            {'role': 'assistant', 'content': 'Server update will begin at 2 AM.'},  
            {'role': 'assistant', 'content': 'Update in progress, estimated time to completion is 45 minutes.'}  
        ]  
    } 
    # async with on the awaited connect
    async with websockets.connect(uri) as ws:
        await ws.send(json.dumps(msg))
        print("Sent:", json.dumps(msg))

if __name__ == "__main__":
    asyncio.run(main())