from locust import HttpUser, task, between


class ApiUser(HttpUser):
    wait_time = between(0.1, 0.5)

    @task
    def create_simulation(self):
        payload = {"target": "LoadTestTarget", "update_every": 50}
        with self.client.post("/api/v1/simulations", json=payload, catch_response=True) as resp:
            if resp.status_code != 200:
                resp.failure(f"unexpected status {resp.status_code}")
