import random
from locust import HttpUser, task, between

class EnterpriseAPIUser(HttpUser):
    wait_time = between(0.2, 0.5)

    # 1. Root System Check
    @task(2)
    def read_root(self):
        self.client.get("/")

    # 2. Health Probes
    @task(1)
    def liveness_check(self):
        self.client.get("/health/liveness")

    @task(1)
    def readiness_check(self):
        self.client.get("/health/readiness")

    # 3. Analytics (Cached BigQuery)
    @task(4)
    def read_analytics(self):
        self.client.get("/analytics/device-breakdown")

    # 4. Telemetry Ingestion
    @task(10)
    def send_telemetry(self):
        payload = {
            "device_id": f"dev_{random.randint(100, 999)}",
            "event_type": random.choice(["click", "view", "error", "purchase"]),
            "timestamp": "2026-07-27T12:00:00Z",
            "metadata": {"session_id": "locust_test"}
        }
        self.client.post("/telemetry", json=payload)

    # 5. Batch Telemetry Ingestion
    @task(3)
    def send_batch_telemetry(self):
        payload = {
            "events": [
                {
                    "device_id": f"dev_{random.randint(100, 999)}",
                    "event_type": "batch_click",
                    "timestamp": "2026-07-27T12:00:00Z"
                } for _ in range(5)
            ]
        }
        self.client.post("/telemetry/batch", json=payload)

    # 6. Safe Chained User CRUD Lifecycle (Guarantees record existence)
    @task(2)
    def user_lifecycle(self):
        user_id = f"locust_user_{random.randint(10000, 99999)}"
        user_data = {
            "name": "Load Test Agent",
            "email": f"{user_id}@example.com",
            "role": "tester"
        }
        
        # Create user
        create_res = self.client.post(f"/api/users/{user_id}", json=user_data)
        if create_res.status_code == 200:
            # Read user
            self.client.get(f"/api/users/{user_id}")
            # Update user
            user_data["role"] = "senior_tester"
            self.client.put(f"/api/users/{user_id}", json=user_data)
            # Delete user
            self.client.delete(f"/api/users/{user_id}")

    # 7. AI System Alerts (Hits non-colliding /api/system/alerts path)
    @task(1)
    def trigger_alert(self):
        payload = {
            "severity": "WARNING",
            "message": "Simulated system alert from load test",
            "details": {"source": "locust"}
        }
        self.client.post("/api/system/alerts", json=payload)