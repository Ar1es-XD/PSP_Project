from locust import HttpUser, task, between


class DbPoolUser(HttpUser):
    wait_time = between(0.05, 0.2)

    @task
    def health_check(self):
        with self.client.get("/api/v1/simulations/nonexistent", catch_response=True) as resp:
            if resp.status_code not in (404, 200):
                resp.failure(f"unexpected status {resp.status_code}")
