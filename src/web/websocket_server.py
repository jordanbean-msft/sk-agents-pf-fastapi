import asyncio
import websockets

connected_clients = set()

async def echo(websocket):
    # Register the new client
    connected_clients.add(websocket)
    try:
        async for message in websocket:
            # Broadcast the received message to all clients
            for client in connected_clients:
                if client != websocket:
                    await client.send(message)
    finally:
        # Unregister the client when they disconnect
        connected_clients.remove(websocket)

async def main():
    # Create and run the server within a running event loop
    async with websockets.serve(echo, "localhost", 6789):
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())