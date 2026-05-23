import asyncio
from bless import BlessServer
from bless.backends.characteristic import GATTCharacteristicProperties
from bless.backends.characteristic import GATTAttributePermissions

MESH_SERVICE_UUID = "12345678-1234-5678-1234-56789abcdef0"
MESH_CHAR_UUID = "12345678-1234-5678-1234-56789abcdef1"

async def advertise():
    server = BlessServer(name="alice-macbook")
    await server.add_new_service(MESH_SERVICE_UUID)
    await server.add_new_characteristic(
        MESH_SERVICE_UUID,
        MESH_CHAR_UUID,
        properties=GATTCharacteristicProperties.read,
        permissions=GATTAttributePermissions.readable,
        value=bytearray(b"hello"),
    )
    await server.start()
    print("Advertising...")
    await asyncio.Event().wait()

asyncio.run(advertise())