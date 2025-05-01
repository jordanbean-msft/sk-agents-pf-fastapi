import asyncio  
import websockets  
  
async def run_client():  
    uri = "ws://localhost:6789"  
    async with websockets.connect(uri) as websocket:  
        print("Connected to server.")  
        await websocket.send("send_event")  
        print("Sent trigger 'send_event'. Waiting for response ...")  
        response = await websocket.recv()  
        print("Received from server:", response)  
  
if __name__ == "__main__":  
    asyncio.run(run_client())  