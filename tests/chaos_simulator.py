import time
import json
import random
from google.cloud import pubsub_v1

PROJECT_ID = "flash-gasket-486800-p9"
TOPIC_ID = "telemetry-stream"  # Ensure this matches your Phase 2 Pub/Sub topic name

publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path(PROJECT_ID, TOPIC_ID)

print("💥 Kicking off Chaos Test: Injecting 30 anomalous error events into Pub/Sub...\n")

device_types = ["Apple_Vision_Pro", "Oculus_Quest_3", "Desktop_WebXR"]

for i in range(30):
    corrupt_payload = {
        "user_id": f"anomaly_user_{i}",
        "session_id": "session_crash_loop_99",
        "event_type": "system_crash_critical",  # Critical error event type
        "device_type": random.choice(device_types),
        "coordinate_x": 99999.9,  # Severe out-of-bounds coordinate
        "coordinate_y": -99999.9,
        "coordinate_z": 0.0
    }
    
    data = json.dumps(corrupt_payload).encode("utf-8")
    future = publisher.publish(topic_path, data)
    print(f"[{i+1}/30] Published anomaly event ID: {future.result()}")
    time.sleep(0.05)

print("\n✅ Ingestion stream finished! Pausing 10s to let Cloud Functions load BigQuery...")
time.sleep(10)
print("👉 Now run: python analytics_agent.py")