import os
from dotenv import load_dotenv

load_dotenv()

INFLUXDB_URL: str = os.getenv("INFLUXDB_URL", "http://localhost:8086")
INFLUXDB_TOKEN: str = os.getenv("INFLUXDB_TOKEN", "changeme")
INFLUXDB_ORG: str = os.getenv("INFLUXDB_ORG", "smartcity")
INFLUXDB_BUCKET: str = os.getenv("INFLUXDB_BUCKET", "sensors")
GRAFANA_ADMIN_PASSWORD: str = os.getenv("GRAFANA_ADMIN_PASSWORD", "admin")
