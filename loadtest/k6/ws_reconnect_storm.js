import ws from "k6/ws";
import { check, sleep } from "k6";

export const options = {
    vus: 1000,
    duration: "2m",
    thresholds: {
        checks: ["rate>0.9"]
    }
};

const wsBase = __ENV.WS_BASE_URL || "ws://localhost:8001";
const simulationId = __ENV.SIMULATION_ID || "demo";

export default function () {
    const sessionId = `${__VU}-${__ITER}`;
    const url = `${wsBase}/ws/simulations/${simulationId}?session_id=${sessionId}&resume=1`;
    const res = ws.connect(url, (socket) => {
        socket.on("open", () => {
            socket.send("ping");
        });

        socket.on("message", () => {
            socket.send("pong");
            socket.close();
        });
    });

    check(res, { "connected": (r) => r && r.status === 101 });
    sleep(0.2);
}
