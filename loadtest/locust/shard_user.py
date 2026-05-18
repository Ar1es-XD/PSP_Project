from locust import HttpUser, task, between


class ShardUser(HttpUser):
    wait_time = between(0.1, 0.3)

    @task
    def shard_skew(self):
        payload = {"target": "ShardTarget", "update_every": 10}
        with self.client.post("/api/v1/simulations", json=payload, catch_response=True) as resp:
            if resp.status_code != 200:
                resp.failure(f"unexpected status {resp.status_code}")
