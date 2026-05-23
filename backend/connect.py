## Jake’s mac: A0:78:17:60:33:FC
## Shree’s mac: 84:2F:57:22:74:35
import asyncio
import argparse
from bleak import BleakClient, BleakError

# On macOS, you need to use the UUID-based address, not the hardware MAC address.
# You can find this by running a scanner script (like test.py) first.
# I'll leave this here as an example of what a macOS address looks like.
EXAMPLE_MACOS_ADDRESS = "XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX"

async def main(address: str):
    """
    Connects to a BLE device at the given address and lists its services.
    """
    print(f"Attempting to connect to {address}...")

    # The `async with` statement ensures that the client is properly
    # disconnected when the block is exited, even if an error occurs.
    try:
        async with BleakClient(address) as client:
            if client.is_connected:
                print(f"Connected to {address}")
                print("Services:")
                # Loop through all services in the client
                for service in client.services:
                    print(f"  [Service] {service.uuid}: {service.description}")
                    # And loop through all characteristics in the service
                    for char in service.characteristics:
                        print(f"    [Characteristic] {char.uuid}: {char.description}, Properties: {char.properties}")
            else:
                # This path is less common with `async with` but good to have
                print(f"Failed to connect to {address}")

    except BleakError as e:
        print(f"Error: Could not connect to device. {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Connect to a BLE device and list its services.")
    parser.add_argument(
        "address",
        help=f"The address of the BLE device to connect to (on macOS, this is a UUID).",
    )
    args = parser.parse_args()

    asyncio.run(main(args.address))