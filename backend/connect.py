## Jake’s mac: A0:78:17:60:33:FC
## Shree’s mac: 84:2F:57:22:74:35

from bleak import BleakClient
import asyncio

connect_address =  "84:2F:57:22:74:35"
async def main(connect_address):
    async with BleakClient(connect_address) as client:
        name = client.name
        print(name)
        if name is None:
            print("Failed to connect")
        return name
name = asyncio.run(main(connect_address))