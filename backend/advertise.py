import asyncio
from bleak import BleakServer

MESH_SERVICE_UUID = "12345678-1234-5678-1234-56789abcdef0"

async def advertise():
    server = BleakServer()
    await server.start(
        service_uuids=[MESH_SERVICE_UUID],
        local_name="shree-macbook"
    )
    print("Advertising...")
    await asyncio.Event().wait()

asyncio.run(advertise())