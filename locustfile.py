from locust import HttpUser, task, between
import random

class APIUser(HttpUser):
    # Wait between 0.5 and 2 seconds between simulated actions per user
    wait_time = between(0.5, 2.0)

    @task(3)  # Higher weight: read requests are typically more frequent
    def get_health_check(self):
        self.client.get("/")

    @task(2)
    def get_analytics(self):
        self.client.get("/analytics/device-breakdown")

    @task(1)
    def post_telemetry(self):
        payload = {
            "user_id": f"user_{random.randint(1, 1000)}",
            "device": random.choice(["iOS", "Android", "WebXR", "Desktop"]),
            "event_type": "click"
        }
        self.client.post("/telemetry", json=payload)