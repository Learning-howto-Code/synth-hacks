import asyncio
from bless import BlessServer

MESH_SERVICE_UUID = "12345678-1234-5678-1234-56789abcdef0"
MESH_CHAR_UUID = "12345678-1234-5678-1234-56789abcdef1"

async def advertise():
    server = BlessServer(name="shree-macbook")
    await server.add_new_service(MESH_SERVICE_UUID)
    await server.add_new_characteristic(
        MESH_SERVICE_UUID,
        MESH_CHAR_UUID,
        properties=0x02 | 0x08,  # read | write
        value=bytearray(b"hello"),
        permissions=0x01 | 0x02
    )
    await server.start()
    print("Advertising...")
    await asyncio.Event().wait()

asyncio.run(advertise())