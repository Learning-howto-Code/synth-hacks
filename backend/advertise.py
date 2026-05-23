import asyncio
from bless import BlessServer
from bless.backends.characteristic import GATTCharacteristicProperties
from bless.backends.characteristic import GATTAttributePermissions

MESH_SERVICE_UUID = "12345678-1234-5678-1234-56789abcdef0"
MESH_CHAR_UUID = "12345678-1234-5678-1234-56789abcdef1"

async def run_server():
    """
    Sets up and runs the BLE server, advertising a single service and characteristic.
    """
    server_name = "Yuvas-MacBook-Pro"
    # The `try...finally` block ensures the server is stopped gracefully.
    server = BlessServer(name=server_name)
    try:
        print(f"Setting up BLE server with name '{server_name}'...")
        
        # Add the service
        await server.add_new_service(MESH_SERVICE_UUID)
        
        # Add the characteristic to the service
        await server.add_new_characteristic(
            MESH_SERVICE_UUID,
            MESH_CHAR_UUID,
            properties=GATTCharacteristicProperties.read,
            permissions=GATTAttributePermissions.readable,
            value=bytearray(b"hello"),
        )
        
        print("Starting advertising...")
        await server.start()
        print(f"Advertising '{server_name}' with service {MESH_SERVICE_UUID}")
        print("Server is running. Press Ctrl+C to stop.")
        
        # Keep the server running indefinitely
        await asyncio.Event().wait()
    finally:
        if server.is_advertising:
            await server.stop()

if __name__ == "__main__":
    asyncio.run(run_server())