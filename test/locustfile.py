import random
from locust import HttpUser, task, between

class SafeAPIUser(HttpUser):
    # Wait between 0.2 and 0.5 seconds between requests per user
    wait_time = between(0.2, 0.5)

    # 1. Root System Check
    @task(2)
    def read_root(self):
        self.client.get("/")

    # 2. Liveness Health Probe (Microsecond response)
    @task(1)
    def liveness_check(self):
        self.client.get("/health/liveness")

    # 3. Readiness Health Probe (Hits Firestore ping)
    @task(1)
    def readiness_check(self):
        self.client.get("/health/readiness")

    # 4. Analytics Engine (Hits BigQuery with RAM cache)
    @task(4)
    def read_analytics(self):
        self.client.get("/analytics/device-breakdown")

    # 5. Single Telemetry Event Ingestion (Matches TelemetryPayload schema)
    @task(10)
    def send_telemetry(self):
        payload = {
            "device_id": f"dev_{random.randint(100, 999)}",
            "event_type": random.choice(["click", "view", "error", "purchase"]),
            "timestamp": "2026-07-27T12:00:00Z",
            "metadata": {"session_id": "locust_stable_test"}
        }
        self.client.post("/telemetry", json=payload)

    # 6. Batch Telemetry Ingestion (High efficiency bulk upload)
    @task(3)
    def send_batch_telemetry(self):
        payload = {
            "events": [
                {
                    "device_id": f"dev_{random.randint(100, 999)}",
                    "event_type": "batch_click",
                    "timestamp": "2026-07-27T12:00:00Z",
                    "metadata": {"batch_index": i}
                } for i in range(5)
            ]
        }
        self.client.post("/telemetry/batch", json=payload)