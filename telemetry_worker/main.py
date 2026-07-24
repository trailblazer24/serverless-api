import base64
import json
import datetime
from google.cloud import bigquery

# Initialize BigQuery client
bq_client = bigquery.Client()
TABLE_ID = "flash-gasket-486800-p9.telemetry_data.telemetry_events_optimized"

def sanitize_and_insert(event, context):
    """Triggered by Pub/Sub message."""
    try:
        # Decode Pub/Sub message payload
        if "data" in event:
            pubsub_message = base64.b64decode(event["data"]).decode("utf-8")
            data = json.loads(pubsub_message)
        else:
            data = event

        # Ensure 'timestamp' exists and is valid ISO format
        if not data.get("timestamp"):
            data["timestamp"] = datetime.datetime.now(datetime.timezone.utc).isoformat()

        # Stream row into BigQuery
        errors = bq_client.insert_rows_json(TABLE_ID, [data])
        
        if errors:
            print(f"❌ BigQuery insertion failure: {errors}")
        else:
            print(f"✅ Successfully inserted event into {TABLE_ID}")

    except Exception as e:
        print(f"⚠️ Error processing telemetry event: {str(e)}")