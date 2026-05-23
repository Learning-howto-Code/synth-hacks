import asyncio
from bleak import BleakScanner

MESH_SERVICE_UUID = "12345678-1234-5678-1234-56789abcdef0"

async def scan():
    devices = await BleakScanner.discover(
        5.0,
        service_uuids=[MESH_SERVICE_UUID]
    )
    for d in devices:
        print(f"{d.name} — {d.address}")

asyncio.run(scan())