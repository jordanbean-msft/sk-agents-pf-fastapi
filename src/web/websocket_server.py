import asyncio  
import websockets  
import random  
import json  
  
async def send_data(websocket, path):  
    print("Client connected")  
    async for message in websocket:  
        print(f"Received command from client: {message}")  
        if message == "send_event":  
            data = {"value": random.randint(101, 500)}  
            await websocket.send(json.dumps(data))  
            print(f"Sent data: {data}")  
        else:  
            await websocket.send(json.dumps({"error": "Unknown command"}))  
  
async def main():  
    print("Starting WebSocket server on ws://localhost:6789")  
    async with websockets.serve(send_data, "localhost", 6789):  
        await asyncio.Future()  # run forever  
  
if __name__ == "__main__":  
    asyncio.run(main())  