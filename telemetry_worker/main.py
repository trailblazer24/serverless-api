import base64
import json
import datetime
import functions_framework
from google.cloud import bigquery

# Initialize BigQuery client
bq_client = bigquery.Client()
TABLE_ID = "flash-gasket-486800-p9.telemetry_data.telemetry_events_optimized"

@functions_framework.cloud_event
def sanitize_and_insert(cloud_event):
    """Triggered by a Pub/Sub event via CloudEvents (Gen 2)."""
    try:
        # Extract base64 data payload from CloudEvent message
        pubsub_message = cloud_event.data.get("message", {})
        pubsub_data = pubsub_message.get("data")
        
        if pubsub_data:
            decoded_bytes = base64.b64decode(pubsub_data)
            data = json.loads(decoded_bytes.decode("utf-8"))
        else:
            data = {}

        # Ensure 'timestamp' exists and is valid ISO format for partitioning
        if not data.get("timestamp"):
            data["timestamp"] = datetime.datetime.now(datetime.timezone.utc).isoformat()

        # Stream row into BigQuery optimized table
        errors = bq_client.insert_rows_json(TABLE_ID, [data])
        if errors:
            print(f"❌ BigQuery insertion failure: {errors}")
        else:
            print(f"✅ [Gen 2] Successfully inserted event into {TABLE_ID}")

    except Exception as e:
        print(f"⚠️ Error processing telemetry event: {str(e)}")