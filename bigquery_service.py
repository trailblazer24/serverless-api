import json
import os
import time
from google.cloud import secretmanager
from google.cloud import bigquery
from cachetools import TTLCache


class BigQueryService:
    def __init__(self):
        self.project_id = os.getenv("GCP_PROJECT_ID", "flash-gasket-486800-p9")
        
        # 1. Initialize In-Memory Cache (TTL: 60 seconds, Max 100 items)
        self.cache = TTLCache(maxsize=100, ttl=60)
        
        # 2. Load secrets FIRST so we have the correct dataset location
        self._load_secrets()
        
        # 3. Instantiate the BigQuery client with the dynamic location
        self.client = bigquery.Client(
            project=self.project_id, 
            location=self.location
        )

    def _load_secrets(self):
        """Fetches runtime configurations securely from GCP Secret Manager."""
        try:
            client = secretmanager.SecretManagerServiceClient()
            secret_name = f"projects/{self.project_id}/secrets/PROJECT_CONFIG/versions/latest"
            response = client.access_secret_version(name=secret_name)
            
            payload = json.loads(response.payload.data.decode("UTF-8"))
            self.dataset_id = payload.get("DATASET_ID", "telemetry_data")
            self.table_id = payload.get("TABLE_ID", "telemetry_events")
            self.location = payload.get("DATASET_LOCATION", "northamerica-northeast1")
            
            print(f"DEBUG: Config loaded successfully -> Dataset: {self.dataset_id}, Table: {self.table_id}, Location: {self.location}")
        except Exception as e:
            print(f"Warning: Could not fetch from Secret Manager: {e}")
            self.dataset_id = "telemetry_data"
            self.table_id = "telemetry_events"
            self.location = "northamerica-northeast1"

    def get_device_breakdown(self) -> dict:
        """
        Fetches device breakdown metrics.
        Uses in-memory TTL cache to resolve repeated hits in <15ms.
        """
        cache_key = "device_breakdown_metrics"

        if cache_key in self.cache:
            cached_data = self.cache[cache_key]
            return {
                "status": "success",
                "source": "in-memory-cache",
                "data": cached_data
            }

        query = f"""
            SELECT 
                device_type, 
                COUNT(*) as event_count
            FROM 
                `{self.project_id}.{self.dataset_id}.{self.table_id}`
            GROUP BY 
                device_type
            ORDER BY 
                event_count DESC
            LIMIT 10
        """
        try:
            query_job = self.client.query(query)
            results = query_job.result()
            
            data = [{"device_type": row.device_type, "event_count": row.event_count} for row in results]
            
            # Save results into RAM cache for the next 60 seconds
            self.cache[cache_key] = data

            return {
                "status": "success",
                "source": "bigquery-live",
                "data": data
            }
        except Exception as e:
            print(f"Error executing BigQuery request: {e}")
            return {
                "status": "error",
                "source": "bigquery-live",
                "message": str(e),
                "data": []
            }


# Instantiate the service so main.py can call it directly
bq_service = BigQueryService()

def get_device_breakdown():
    result = bq_service.get_device_breakdown()
    return result.get("data", [])