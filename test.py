"""
Scan/Discovery
--------------

Example showing how to scan for BLE devices.

Updated on 2019-03-25 by hbldh <henrik.blidh@nedomkull.com>

"""

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

    # Filter by RSSI if a threshold is provided by the user
    if args.rssi:
        devices = {
            addr: (d, a) for addr, (d, a) in devices.items() if d.rssi >= args.rssi
        }

    if not devices:
        print("No devices found.")
        return

    # Sort by signal strength (RSSI) to show closest devices first
    for d, a in sorted(devices.values(), key=lambda x: x[0].rssi, reverse=True):
        # Attempt to get a friendly name for the device, falling back to "Unknown"
        name = a.local_name or d.name or "Unknown Device"
        print()
        print(f"Device: {name} ({d.address})")
        print(f"  RSSI: {d.rssi} dBm, TX Power: {a.tx_power}")
        if a.service_uuids:
            print(f"  Service UUIDs: {', '.join(a.service_uuids)}")
        if a.manufacturer_data:
            # Show manufacturer data, formatted for readability
            for mfg_id, mfg_data in a.manufacturer_data.items():
                print(f"  Manufacturer: {mfg_id}, Data: {mfg_data.hex()}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--services",
        metavar="<uuid>",
        nargs="*",
        help="UUIDs of one or more services to filter for",
    )

    parser.add_argument(
        "--rssi",
        metavar="<dbm>",
        type=int,
        help="Filter by RSSI threshold, e.g., -60 to show only strong signals",
    )

    parser.add_argument(
        "--macos-use-bdaddr",
        action="store_true",
        help="when true use Bluetooth address instead of UUID on macOS",
    )

    args = parser.parse_args()

    asyncio.run(main(args))