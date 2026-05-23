import asyncio
from bleak import BleakScanner

# The MESH_SERVICE_UUID is not needed for a general scan
# MESH_SERVICE_UUID = "12345678-1234-5678-1234-56789abcdef0"

async def scan():
    print("Scanning for 'Jakes-Macbook' for 5 seconds...")
    # We remove the `serviceids` filter to find all advertising devices.
    devices = await BleakScanner.discover(
        timeout=5.0,
    )
    for d in devices:
        # The advertising script sets the name, so we can look for it.
        if d.name == "Jakes-Macbook":
            print(f"Found: {d.name} — {d.address}")

asyncio.run(scan())