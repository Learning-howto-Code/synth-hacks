"""
Scan/Discovery
--------------

Example showing how to scan for BLE devices.

Updated on 2019-03-25 by hbldh <henrik.blidh@nedomkull.com>

"""
## Jake’s mac: A0:78:17:60:33:FC
## Shree’s mac: 84:2F:57:22:74:35
import argparse
import asyncio

from bleak import BleakScanner

async def main(args: argparse.Namespace):
    print("scanning for 5 seconds, please wait...")

    devices = await BleakScanner.discover(
        timeout=5.0,
        return_adv=True,
        service_uuids=args.services,
        use_bdaddr=args.macos_use_bdaddr,
    )

    if not devices:
        print("No devices found.")
        return

    for d, a in sorted(devices.values(), key=lambda x: x[0].address):
        print()
        print(d)
        print("-" * len(str(d)))
        print(a)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--services",
        metavar="<uuid>",
        nargs="*",
        help="UUIDs of one or more services to filter for",
    )

    parser.add_argument(
        "--macos-use-bdaddr",
        action="store_true",
        help="when true use Bluetooth address instead of UUID on macOS",
    )

    args = parser.parse_args()

    asyncio.run(main(args))