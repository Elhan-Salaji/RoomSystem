#!/usr/bin/env python3
"""
Standalone seeder for OccuPi InfluxDB 3 Core.
Writes 7 days of realistic occupancy data directly via HTTP — no Spring needed.

Usage:
    python3 docker/seed.py

Requirements: Python 3.8+, no extra packages needed.
"""

import urllib.request
import urllib.error
import math
import random
import sys
from datetime import datetime, timezone, timedelta

# ── Config ────────────────────────────────────────────────────────────────────
INFLUX_URL  = "http://localhost:8181"
DATABASE    = "occupi"
MEASUREMENT = "occupancy"
DAYS_BACK   = 7
INTERVAL_MIN = 5
BATCH_LINES  = 500

ROOMS = [
    ("seminar-101",    "sensor-A",  30),
    ("seminar-102",    "sensor-B",  30),
    ("lecture-hall-1", "sensor-C", 120),
    ("library-reading","sensor-D",  50),
    ("cafeteria",      "sensor-E",  80),
]

# ── Helpers ───────────────────────────────────────────────────────────────────

def weekday_pattern(hour: int, rng: random.Random) -> float:
    if   hour <  7: base = 0.00
    elif hour <  9: base = 0.10 + (hour - 7) * 0.15
    elif hour < 12: base = 0.60 + (hour - 9) * 0.10
    elif hour < 13: base = 0.40
    elif hour < 16: base = 0.65 + (hour - 13) * 0.05
    elif hour < 19: base = 0.65 - (hour - 16) * 0.15
    elif hour < 21: base = 0.15
    else:           base = 0.02
    return max(0.0, min(1.0, base + rng.gauss(0, 0.08)))


def weekend_pattern(hour: int, rng: random.Random) -> float:
    if   hour <  9: base = 0.00
    elif hour < 12: base = 0.10 + (hour - 9) * 0.05
    elif hour < 16: base = 0.20
    else:           base = 0.05
    return max(0.0, min(1.0, base + rng.gauss(0, 0.05)))


def simulate_count(ts: datetime, capacity: int, rng: random.Random) -> int:
    hour = ts.hour
    is_weekend = ts.weekday() >= 5
    ratio = weekend_pattern(hour, rng) if is_weekend else weekday_pattern(hour, rng)
    return max(0, min(capacity, round(ratio * capacity)))


def write_batch(lines: list[str]) -> None:
    body = "\n".join(lines).encode("utf-8")
    url  = f"{INFLUX_URL}/api/v2/write?bucket={DATABASE}&precision=ns"
    req  = urllib.request.Request(url, data=body, method="POST")
    req.add_header("Content-Type", "text/plain; charset=utf-8")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status not in (200, 204):
                print(f"  ⚠  Unexpected HTTP {resp.status}", file=sys.stderr)
    except urllib.error.HTTPError as e:
        print(f"  ✗  HTTP {e.code}: {e.read().decode()}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"  ✗  Cannot reach InfluxDB at {INFLUX_URL}: {e.reason}", file=sys.stderr)
        print("     → Is Docker running?  docker compose -f docker/docker-compose.yml up -d", file=sys.stderr)
        sys.exit(1)


def check_already_seeded() -> bool:
    url = f"{INFLUX_URL}/api/v3/query_sql?db={DATABASE}&q=SELECT+count+FROM+{MEASUREMENT}+LIMIT+1"
    try:
        with urllib.request.urlopen(url, timeout=5) as resp:
            body = resp.read().decode()
            return len(body.strip()) > 2  # non-empty JSON array
    except Exception:
        return False

# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    print("OccuPi Data Seeder")
    print("==================")

    # Health check
    try:
        with urllib.request.urlopen(f"{INFLUX_URL}/health", timeout=5) as r:
            print(f"✓ InfluxDB reachable (HTTP {r.status})")
    except Exception as e:
        print(f"✗ InfluxDB not reachable at {INFLUX_URL}: {e}")
        print("  → Make sure Docker is running:  docker compose -f docker/docker-compose.yml up -d")
        sys.exit(1)

    if check_already_seeded():
        print("✓ Data already exists — skipping seed to avoid duplicates.")
        print("  To re-seed, drop the measurement first:")
        print(f'  curl -G "{INFLUX_URL}/api/v3/query_sql" --data-urlencode "db={DATABASE}" \\')
        print(f'       --data-urlencode "q=DROP TABLE {MEASUREMENT}"')
        return

    rng   = random.Random(42)
    now   = datetime.now(timezone.utc)
    start = (now - timedelta(days=DAYS_BACK)).replace(hour=0, minute=0, second=0, microsecond=0)

    total_points = 0
    batch: list[str] = []

    print(f"Generating {DAYS_BACK} days × {len(ROOMS)} rooms @ {INTERVAL_MIN}-min intervals …")

    for room_id, sensor_id, capacity in ROOMS:
        ts = start
        while ts < now:
            count      = simulate_count(ts, capacity, rng)
            confidence = round(0.75 + rng.random() * 0.25, 2)
            ns         = int(ts.timestamp() * 1_000_000_000)

            # InfluxDB line protocol:
            # measurement,tag1=v1,tag2=v2 field1=v1i,field2=v2 timestamp_ns
            line = (
                f"{MEASUREMENT},roomId={room_id},sensorId={sensor_id} "
                f"count={count}i,confidence={confidence} "
                f"{ns}"
            )
            batch.append(line)

            if len(batch) >= BATCH_LINES:
                write_batch(batch)
                total_points += len(batch)
                batch.clear()
                print(f"  … {total_points} points written", end="\r")

            ts += timedelta(minutes=INTERVAL_MIN)

    if batch:
        write_batch(batch)
        total_points += len(batch)

    print(f"\n✓ Done — {total_points:,} data points written to InfluxDB.")
    print(f"\nOpen Grafana: http://localhost:3001  (admin / admin)")
    print("Dashboard:    Dashboards → OccuPi — Raumbelegung")


if __name__ == "__main__":
    main()
