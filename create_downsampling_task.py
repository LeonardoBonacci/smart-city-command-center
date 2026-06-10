"""
Create an InfluxDB downsampling task.

For demo purposes the task runs every 1 minute and aggregates into 5-minute
windows (instead of hourly). This lets you see results within a few minutes
of running the ingestion script. The pattern is identical to a production
hourly downsampling task — just swap the intervals.
"""

import requests
from config import INFLUXDB_URL, INFLUXDB_TOKEN, INFLUXDB_ORG, INFLUXDB_BUCKET

DOWNSAMPLED_BUCKET = "sensors_downsampled"

HEADERS = {
    "Authorization": f"Token {INFLUXDB_TOKEN}",
    "Content-Type": "application/json",
}


def create_bucket() -> None:
    """Create the downsampled bucket if it doesn't already exist."""
    # Get org ID
    resp = requests.get(
        f"{INFLUXDB_URL}/api/v2/orgs",
        headers=HEADERS,
        params={"org": INFLUXDB_ORG},
    )
    resp.raise_for_status()
    org_id = resp.json()["orgs"][0]["id"]

    # Check if bucket already exists
    resp = requests.get(
        f"{INFLUXDB_URL}/api/v2/buckets",
        headers=HEADERS,
        params={"name": DOWNSAMPLED_BUCKET, "orgID": org_id},
    )
    if resp.status_code == 200 and resp.json().get("buckets"):
        print(f"✓ Bucket '{DOWNSAMPLED_BUCKET}' already exists")
        return

    # Create the bucket
    resp = requests.post(
        f"{INFLUXDB_URL}/api/v2/buckets",
        headers=HEADERS,
        json={
            "name": DOWNSAMPLED_BUCKET,
            "orgID": org_id,
            "retentionRules": [{"type": "expire", "everySeconds": 30 * 86400}],
        },
    )
    resp.raise_for_status()
    print(f"✓ Created bucket '{DOWNSAMPLED_BUCKET}' (30-day retention)")


def create_task() -> None:
    """Create the downsampling task (every 1m, 5-minute aggregation windows)."""
    # Flux script: downsample air_quality, traffic, and weather measurements
    flux_script = f"""
option task = {{name: "downsample_sensors", every: 1m}}

data = from(bucket: "{INFLUXDB_BUCKET}")
    |> range(start: -task.every)

data
    |> aggregateWindow(every: 5m, fn: mean, createEmpty: false)
    |> to(bucket: "{DOWNSAMPLED_BUCKET}", org: "{INFLUXDB_ORG}")
"""

    # Check if task already exists
    resp = requests.get(
        f"{INFLUXDB_URL}/api/v2/tasks",
        headers=HEADERS,
        params={"name": "downsample_sensors", "org": INFLUXDB_ORG},
    )
    resp.raise_for_status()
    existing = [t for t in resp.json().get("tasks", []) if t["name"] == "downsample_sensors"]
    if existing:
        # Delete old version so we can recreate with updated script
        for task in existing:
            requests.delete(
                f"{INFLUXDB_URL}/api/v2/tasks/{task['id']}",
                headers=HEADERS,
            )
        print("✓ Removed old task version")

    # Create the task
    resp = requests.post(
        f"{INFLUXDB_URL}/api/v2/tasks",
        headers=HEADERS,
        json={
            "org": INFLUXDB_ORG,
            "flux": flux_script.strip(),
            "status": "active",
        },
    )
    resp.raise_for_status()
    task_id = resp.json()["id"]
    print(f"✓ Created task 'downsample_sensors' (id: {task_id})")
    print("  → Runs every 1 minute, aggregates into 5-minute mean windows")
    print(f"  → Writes to bucket '{DOWNSAMPLED_BUCKET}'")


if __name__ == "__main__":
    print("Setting up InfluxDB downsampling task...\n")
    create_bucket()
    create_task()
    print("\nDone! The task will fire every minute.")
    print("Check results: InfluxDB UI → Data Explorer → select 'sensors_downsampled' bucket")
