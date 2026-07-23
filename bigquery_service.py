import json
import os
from google.cloud import secretmanager
from google.cloud import bigquery

class BigQueryService:
    def __init__(self):
        self.project_id = os.getenv("GCP_PROJECT_ID", "flash-gasket-486800-p9")
        
        # 1. Load secrets FIRST so we have the correct dataset location
        self._load_secrets()
        
        # 2. Instantiate the BigQuery client with the dynamic location
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
            self.location = payload.get("DATASET_LOCATION", "northamerica-northeast1") # [cite: 164, 168]
            
            print(f"DEBUG: Config loaded successfully -> Dataset: {self.dataset_id}, Table: {self.table_id}, Location: {self.location}")
        except Exception as e:
            print(f"Warning: Could not fetch from Secret Manager: {e}")
            self.dataset_id = "telemetry_data"
            self.table_id = "telemetry_events"
            self.location = "northamerica-northeast1" # [cite: 164, 168]

    def get_device_breakdown(self) -> list:
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
            return [{"device_type": row.device_type, "event_count": row.event_count} for row in results]
        except Exception as e:
            print(f"Error executing BigQuery request: {e}")
            return []