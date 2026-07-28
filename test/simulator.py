import time
import json
import random
from datetime import datetime, timezone
from google.cloud import pubsub_v1

PROJECT_ID = "flash-gasket-486800-p9"
TOPIC_ID = "telemetry-stream"

publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path(PROJECT_ID, TOPIC_ID)

print(f"Telemetry Simulator Ignited! Publishing messages to {topic_path}...")
print("Press Ctrl+C to terminate the simulator.")

user_sessions = [f"user_{random.randint(1000, 9999)}" for _ in range(5)]

try:
    while True:
        user_id = random.choice(user_sessions)

        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "user_id": user_id,
            "session_id": f"sess_{user_id.split('_')[1]}",
            "event_type": random.choice(["player_movement", "item_interaction", "ui_click"]),
            "coordinate_x": round(random.uniform(-50.0, 50.0), 4),
            "coordinate_y": round(random.uniform(0.0, 10.0), 4),
            "coordinate_z": round(random.uniform(-50.0, 50.0), 4),
            "device_type": random.choice(["Oculus_Quest_3", "Apple_Vision_Pro", "Desktop_WebXR"])
        }

        data_bytes = json.dumps(payload).encode("utf-8")

        future = publisher.publish(topic_path, data_bytes)
        message_id = future.result()

        print(f"Sent {payload['event_type']} for {user_id} with message ID: {message_id}")

        time.sleep(random.uniform(0.5, 2.0))

except KeyboardInterrupt:
    print("\nTelemetry Simulator terminated by user.")