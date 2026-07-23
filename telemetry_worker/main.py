import base64
import json
import os
from google.cloud import bigquery
import functions_framework

bq_client = bigquery.Client()
TABLE_REF = "flash-gasket-486800-p9.telemetry_data.device_telemetry"

@functions_framework.cloud_event
def stream_to_bigquery(cloud_event):
    """Triggered by a CloudEvent from a Pub/Sub message topic."""
    
    # Access and decode the base64 Pub/Sub payload
    pubsub_message = cloud_event.data["message"]
    if "data" not in pubsub_message:
        print("⚠️ No data block found in message payload.")
        return

    raw_data = base64.b64decode(pubsub_message["data"]).decode("utf-8")
    event_json = json.loads(raw_data)
    
    print(f"📥 Processing event for user: {event_json.get('user_id')}")

    coords = event_json.get("coordinates", {})
    
    row_to_insert = {
        "timestamp": event_json.get("timestamp"),
        "user_id": event_json.get("user_id"),
        "session_id": event_json.get("session_id"),
        "event_type": event_json.get("event_type"),
        "coordinate_x": coords.get("x"),
        "coordinate_y": coords.get("y"),
        "coordinate_z": coords.get("z"),
        "device_type": event_json.get("device_type")
    }

    errors = bq_client.insert_rows_json(TABLE_REF, [row_to_insert])
    
    if not errors:
        print("✅ Row successfully committed to BigQuery data warehouse.")
    else:
        print(f"❌ BigQuery insertion failure: {errors}")