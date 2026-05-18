import ws from "k6/ws";
import { check, sleep } from "k6";

export const options = {
    vus: 2000,
    duration: "3m",
    thresholds: {
        checks: ["rate>0.95"]
    }
};

const wsBase = __ENV.WS_BASE_URL || "ws://localhost:8001";
const simulationId = __ENV.SIMULATION_ID || "demo";

export default function () {
    const url = `${wsBase}/ws/simulations/${simulationId}`;
    const res = ws.connect(url, (socket) => {
        socket.on("open", () => {
            socket.send("ping");
        });

        socket.on("message", () => {
            socket.send("pong");
        });

        socket.on("close", () => { });

        setTimeout(() => {
            socket.close();
        }, 5000);
    });

    check(res, { "connected": (r) => r && r.status === 101 });
    sleep(1);
}
