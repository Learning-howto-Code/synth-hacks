import asyncio
from bleak import BleakScanner, BleakClient

MESH_SERVICE_UUID = "12345678-1234-5678-1234-56789abcdef0"
MESH_CHAR_UUID = "12345678-1234-5678-1234-56789abcdef1"

async def find_and_connect():
    print("Scanning for device advertising our service...")
    device = await BleakScanner.find_device_by_filter(
        lambda _, adv: MESH_SERVICE_UUID.lower() in [s.lower() for s in adv.service_uuids],
        timeout=10.0,
    )

    if device is None:
        print("Device not found. Is advertise.py running on the other machine?")
        return

    print(f"Found: {device.name} — {device.address}")

    async with BleakClient(device.address) as client:
        print(f"Connected: {client.is_connected}")
        data = await client.read_gatt_char(MESH_CHAR_UUID)
        print(f"Got: {data.decode()}")

asyncio.run(find_and_connect())