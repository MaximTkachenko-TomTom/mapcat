#!/usr/bin/env bash
# Sends location updates tracing a full circle and places a red dot at each point.
# The triangle marker's visual center should coincide with each red dot.
# Usage: bash demo-location-circle.sh | mapcat

set -euo pipefail

CENTER_LAT=52.3731
CENTER_LNG=4.8922
RADIUS_DEG=0.005   # ~500 m radius
STEPS=36           # one point every 10 degrees
DELAY=0.3          # seconds between updates

python3 - <<EOF
import math
import time
import sys

center_lat = $CENTER_LAT
center_lng = $CENTER_LNG
radius     = $RADIUS_DEG
steps      = $STEPS
delay      = $DELAY

# Clear previous state
print("clear", flush=True)
time.sleep(delay)

for i in range(steps + 1):          # +1 closes the loop back to 0 deg
    angle_deg = (i * 360 / steps) % 360
    angle_rad = math.radians(angle_deg)

    # North = 0 deg, clockwise
    lat = center_lat + radius * math.cos(angle_rad)
    lng = center_lng + radius * math.sin(angle_rad) / math.cos(math.radians(center_lat))

    # Red reference dot — its center is the exact geo point
    print(f"add-point ({lat:.6f},{lng:.6f}) color=red radius=4 border=0", flush=True)

    # Location update — triangle should align with this same geo point
    print(f"update-current-position ({lat:.6f},{lng:.6f})", flush=True)

    time.sleep(delay)
EOF
