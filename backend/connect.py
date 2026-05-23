import asyncio
from bleak import BleakClient
from bless import BlessServer
from bless.backends.characteristic import GATTCharacteristicProperties
from bless.backends.characteristic import GATTAttributePermissions

# ID for connecting, shared accross devices
MESH_CHAR_UUID = "12345678-1234-5678-1234-56789abcdef1"
#addres from shree's mac
SHREE_ADDRESS = "6E71AD25-22E7-9C7F-4C80-9A43D1BF88E9"

# Reads from other mac
async def connect():
    async with BleakClient(SHREE_ADDRESS) as client:
        print(f"Connected: {client.is_connected}")

        # Read the characteristic value
        data = await client.read_gatt_char(MESH_CHAR_UUID)
        print(f"Got: {data.decode()}")
    
# Writes to other mac
async def advertise():
    server = BlessServer(name="jake's-macbook")
    await server.add_new_service(MESH_CHAR_UUID)
    await server.add_new_characteristic(
        MESH_CHAR_UUID,
        MESH_CHAR_UUID,
        properties=GATTCharacteristicProperties.read,
        permissions=GATTAttributePermissions.readable,
        value=bytearray(b"test123"),
    )
    await server.start()
    print("Advertising...")
    await asyncio.Event().wait()

asyncio.run(connect())
asyncio.run(advertise())