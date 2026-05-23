import asyncio
from bleak import BleakScanner

MESH_SERVICE_UUID = "12345678-1234-5678-1234-56789abcdef0"

async def scan():
    print("Scanning all devices for 5 seconds...")
    devices = await BleakScanner.discover(
        timeout=5.0,
        return_adv=True,
    )
    found = [
        (d, adv) for d, adv in devices.values()
        if MESH_SERVICE_UUID.lower() in [s.lower() for s in adv.service_uuids]
    ]
    if not found:
        print("No mesh devices found.")
        return
    for d, _ in found:
        print(f"Found: {d.name} — {d.address}")

asyncio.run(scan())