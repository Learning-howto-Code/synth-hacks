import asyncio
from bleak import BleakScanner

MESH_SERVICE_UUID = "12345678-1234-5678-1234-56789abcdef0"

async def scan():
    print("Scanning for mesh service for 5 seconds...")
    devices = await BleakScanner.discover(
        timeout=5.0,
        return_adv=True,
        service_uuids=[MESH_SERVICE_UUID],
    )
    if not devices:
        print("No devices found.")
        return
    for d, _ in devices.values():
        print(f"Found: {d.name} — {d.address}")

asyncio.run(scan())