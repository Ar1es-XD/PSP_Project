import http from "k6/http";
import { check, sleep } from "k6";

export const options = {
    vus: 200,
    duration: "5m",
    thresholds: {
        http_req_failed: ["rate<0.02"],
        http_req_duration: ["p(95)<500", "p(99)<1200"]
    }
};

const baseUrl = __ENV.API_BASE_URL || "http://localhost:8000/api/v1";

export default function () {
    const payload = JSON.stringify({
        target: "LoadTestTarget",
        update_every: 50
    });
    const params = { headers: { "Content-Type": "application/json" } };
    const res = http.post(`${baseUrl}/simulations`, payload, params);
    check(res, {
        "status 200": (r) => r.status === 200
    });
    sleep(0.1);
}
