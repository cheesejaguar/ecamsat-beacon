#!/usr/bin/env python3
"""
Build the static data files for the EcAMSat 2.0 site.

  site/data/beacons.json   the 32 ham-received packets, tagged by station
  site/data/bus.json       2017 bus telemetry, columnar and sorted by bus time
  tests/golden_decode.json the Python decoder's output for every packet,
                           which the JS port in site/decoder.js must match

Usage:
  python3 tools/build_data.py [path/to/bus_data.csv]
"""

import csv
import json
import sys
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from backend.decoder import decode_beacon  # noqa: E402

BEACON_FILE = ROOT / "beacons" / "beacon.txt.txt"
DEFAULT_BUS_CSV = Path.home() / "Documents" / "EcAMSat" / "bus_data.csv"
DAY = 86400

# Columns carried into bus.json, in the order they appear in the CSV
BUS_COLUMNS = [
    "t1", "t2", "t5", "t6", "t7", "t8", "t11", "t12", "payload_1t",
    "solar_1i", "solar_2i", "solar_3i", "solar_4i",
    "solar_1v", "solar_2v", "solar_3v", "solar_4v",
    "comm_i", "sensors_i", "bus_i", "payload_heater_i", "payload_i", "beacon_i",
    "comm_v", "sensors_v", "bus_v", "battery_v",
    "radiation_sensor", "status_byte",
]


def read_beacons():
    """Parse beacon.txt.txt: station callsign lines followed by packets."""
    beacons, station = [], None
    for line in BEACON_FILE.read_text().splitlines():
        line = line.rstrip("\n")
        if line.startswith("EcAMSat.org"):
            beacons.append({"station": station, "packet": line.rstrip()})
        elif line.strip():
            station = line.strip()
    return beacons


def build_beacons(beacons):
    out = ROOT / "site" / "data" / "beacons.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(beacons, indent=1) + "\n")
    return out


def build_golden(beacons):
    golden = []
    for b in beacons:
        decoded = asdict(decode_beacon(b["packet"]))
        golden.append({"packet": b["packet"], "decoded": decoded})

    # Clock check: every ham packet was received just after deployment on
    # 2017-11-20, so its bus time sits ~25-27 days after bus t=0 (~2017-10-25 16:00 UTC).
    for g in golden:
        days = g["decoded"]["bus_time_seconds"] / DAY
        assert 25 <= days <= 27, f"unexpected bus time {days:.2f} d in {g['packet']}"

    out = ROOT / "tests" / "golden_decode.json"
    out.write_text(json.dumps(golden, indent=1) + "\n")
    return out


def build_bus(csv_path):
    with open(csv_path, newline="") as f:
        rows = list(csv.DictReader(f))
    rows.sort(key=lambda r: int(r["time_stamp"]))

    def num(v):
        x = float(v)
        return int(x) if x.is_integer() else round(x, 3)

    data = {
        "source": "EcAMSat bus telemetry, saved 2017-12-07",
        "epoch_note": "bus time 0 is approximately 2017-10-25 16:00 UTC (derived; see BUS_EPOCH_MS in site/decoder.js)",
        "t": [int(r["time_stamp"]) for r in rows],
        **{c: [num(r[c]) for r in rows] for c in BUS_COLUMNS},
    }
    out = ROOT / "site" / "data" / "bus.json"
    out.write_text(json.dumps(data, separators=(",", ":")) + "\n")
    return out, len(rows)


def main():
    csv_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_BUS_CSV
    beacons = read_beacons()
    print(f"beacons: {len(beacons)} -> {build_beacons(beacons).relative_to(ROOT)}")
    print(f"golden:  {len(beacons)} -> {build_golden(beacons).relative_to(ROOT)}")
    if csv_path.exists():
        out, n = build_bus(csv_path)
        print(f"bus:     {n} rows -> {out.relative_to(ROOT)} ({out.stat().st_size // 1024} KB)")
    else:
        print(f"bus:     skipped, {csv_path} not found (existing site/data/bus.json kept)")


if __name__ == "__main__":
    main()
