"""
SmartCity Pulse - Data Ingestion for Downtown Wellington, NZ.

Simulates 10 sensor stations across 4 zones with realistic patterns
for air quality, traffic, and weather measurements.
"""

import math
import random
import time
from datetime import datetime, timezone

from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

from config import INFLUXDB_URL, INFLUXDB_TOKEN, INFLUXDB_ORG, INFLUXDB_BUCKET

# Wellington downtown sensor stations
STATIONS = [
    # Center zone - CBD / commercial
    {"id": "lambton-quay", "zone": "center", "lat": -41.2797, "lon": 174.7746},
    {"id": "courtenay-place", "zone": "center", "lat": -41.2929, "lon": 174.7790},
    {"id": "willis-street", "zone": "center", "lat": -41.2870, "lon": 174.7720},
    # Industrial zone - port / freight area
    {"id": "centreport", "zone": "industrial", "lat": -41.2720, "lon": 174.7880},
    {"id": "kaiwharawhara", "zone": "industrial", "lat": -41.2620, "lon": 174.7780},
    # Residential zone
    {"id": "mt-victoria", "zone": "residential", "lat": -41.2960, "lon": 174.7880},
    {"id": "kelburn", "zone": "residential", "lat": -41.2850, "lon": 174.7650},
    {"id": "aro-valley", "zone": "residential", "lat": -41.2920, "lon": 174.7670},
    # Park zone - green spaces / waterfront
    {"id": "botanic-gardens", "zone": "park", "lat": -41.2810, "lon": 174.7660},
    {"id": "waterfront", "zone": "park", "lat": -41.2860, "lon": 174.7810},
]

# Zone-based baselines for air quality (PM2.5 ug/m3)
ZONE_PM25_BASELINE = {
    "center": 18.0,
    "industrial": 28.0,
    "residential": 10.0,
    "park": 6.0,
}

ZONE_PM10_BASELINE = {
    "center": 30.0,
    "industrial": 45.0,
    "residential": 18.0,
    "park": 12.0,
}

ZONE_NO2_BASELINE = {
    "center": 25.0,
    "industrial": 35.0,
    "residential": 12.0,
    "park": 8.0,
}

# Traffic baseline (vehicles/min)
ZONE_TRAFFIC_BASELINE = {
    "center": 40,
    "industrial": 25,
    "residential": 12,
    "park": 8,
}


def get_hour_factor(hour: float) -> float:
    """Rush-hour multiplier: peaks at 7-9am and 5-7pm."""
    morning_peak = math.exp(-((hour - 8) ** 2) / 2.0)
    evening_peak = math.exp(-((hour - 17.5) ** 2) / 2.0)
    # Base activity level with rush-hour spikes
    return 1.0 + 1.5 * morning_peak + 1.8 * evening_peak


def get_temperature(hour: float) -> float:
    """Diurnal temperature for Wellington (mild maritime climate, 8-18°C range)."""
    # Min around 5am, max around 2pm
    base = 13.0  # Wellington average
    amplitude = 5.0
    return base + amplitude * math.sin((hour - 5) * math.pi / 12.0)


def get_wind_speed(hour: float) -> float:
    """Wellington is famously windy - simulate gusty conditions."""
    base = 25.0  # km/h - Wellington's notorious wind
    variation = 15.0 * math.sin(hour * math.pi / 8.0)
    gust = random.uniform(-10, 20)
    return max(5.0, base + variation + gust)


def get_humidity(hour: float, temperature: float) -> float:
    """Humidity inversely correlated with temperature."""
    base = 75.0  # Wellington is fairly humid
    temp_effect = -(temperature - 13.0) * 2.0
    return max(40.0, min(98.0, base + temp_effect + random.uniform(-5, 5)))


def generate_air_quality_points(station: dict, now: datetime, hour_factor: float) -> list[Point]:
    """Generate air quality measurement points."""
    zone = station["zone"]
    noise = random.uniform(0.8, 1.2)

    pm25 = ZONE_PM25_BASELINE[zone] * hour_factor * noise
    pm10 = ZONE_PM10_BASELINE[zone] * hour_factor * random.uniform(0.85, 1.15)
    no2 = ZONE_NO2_BASELINE[zone] * hour_factor * random.uniform(0.9, 1.1)

    # Wind dispersal effect (Wellington wind reduces pollution)
    wind = get_wind_speed(now.hour + now.minute / 60.0)
    wind_factor = max(0.5, 1.0 - (wind - 20) * 0.01)
    pm25 *= wind_factor
    pm10 *= wind_factor
    no2 *= wind_factor

    point = (
        Point("air_quality")
        .tag("station", station["id"])
        .tag("zone", zone)
        .tag("lat", str(station["lat"]))
        .tag("lon", str(station["lon"]))
        .field("pm25", round(max(1.0, pm25), 2))
        .field("pm10", round(max(2.0, pm10), 2))
        .field("no2", round(max(1.0, no2), 2))
        .time(now, WritePrecision.S)
    )
    return [point]


def generate_traffic_points(station: dict, now: datetime, hour_factor: float) -> list[Point]:
    """Generate traffic measurement points."""
    zone = station["zone"]
    baseline = ZONE_TRAFFIC_BASELINE[zone]

    vehicles_per_min = int(baseline * hour_factor * random.uniform(0.7, 1.3))
    avg_speed_kmh = max(5, int(50 - (hour_factor - 1.0) * 15 + random.uniform(-8, 8)))
    congestion_pct = min(100, max(0, int((hour_factor - 1.0) * 40 + random.uniform(-10, 10))))

    point = (
        Point("traffic")
        .tag("station", station["id"])
        .tag("zone", zone)
        .field("vehicles_per_min", vehicles_per_min)
        .field("avg_speed_kmh", avg_speed_kmh)
        .field("congestion_pct", congestion_pct)
        .time(now, WritePrecision.S)
    )
    return [point]


def generate_weather_points(station: dict, now: datetime) -> list[Point]:
    """Generate weather measurement points."""
    hour = now.hour + now.minute / 60.0
    temperature = get_temperature(hour) + random.uniform(-1.0, 1.0)
    humidity = get_humidity(hour, temperature)
    wind_speed = get_wind_speed(hour)
    # Wellington wind direction predominantly northerly or southerly
    wind_direction = random.choice([0, 180]) + random.uniform(-45, 45)
    wind_direction = wind_direction % 360
    # Pressure typical for Wellington
    pressure_hpa = 1013.0 + random.uniform(-5, 5)

    point = (
        Point("weather")
        .tag("station", station["id"])
        .tag("zone", station["zone"])
        .field("temperature_c", round(temperature, 1))
        .field("humidity_pct", round(humidity, 1))
        .field("wind_speed_kmh", round(wind_speed, 1))
        .field("wind_direction_deg", round(wind_direction, 1))
        .field("pressure_hpa", round(pressure_hpa, 1))
        .time(now, WritePrecision.S)
    )
    return [point]


def main():
    print("SmartCity Pulse - Wellington Downtown Data Ingestion")
    print(f"Connecting to InfluxDB at {INFLUXDB_URL}...")

    client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)
    write_api = client.write_api(write_options=SYNCHRONOUS)

    # Verify connection
    health = client.health()
    if health.status != "pass":
        print(f"InfluxDB health check failed: {health.message}")
        return
    print(f"Connected. Writing to bucket '{INFLUXDB_BUCKET}'")
    print(f"Stations: {len(STATIONS)} across 4 zones (center, industrial, residential, park)")
    print("Press Ctrl+C to stop.\n")

    batch_count = 0
    try:
        while True:
            now = datetime.now(timezone.utc)
            hour = now.hour + now.minute / 60.0
            hour_factor = get_hour_factor(hour)

            points = []
            for station in STATIONS:
                points.extend(generate_air_quality_points(station, now, hour_factor))
                points.extend(generate_traffic_points(station, now, hour_factor))
                points.extend(generate_weather_points(station, now))

            write_api.write(bucket=INFLUXDB_BUCKET, record=points)
            batch_count += 1

            local_time = now.astimezone().strftime("%H:%M:%S")
            print(
                f"[{local_time}] Batch #{batch_count}: "
                f"{len(points)} points written | "
                f"hour_factor={hour_factor:.2f} | "
                f"stations={len(STATIONS)}"
            )

            time.sleep(10)

    except KeyboardInterrupt:
        print(f"\nStopped. Total batches written: {batch_count}")
    finally:
        client.close()


if __name__ == "__main__":
    main()
