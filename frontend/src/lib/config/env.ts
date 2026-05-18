type EnvConfig = {
    apiBaseUrl: string;
    wsBaseUrl: string;
};

function readEnv(key: string, fallback: string): string {
    return process.env[key] ?? fallback;
}

export const env: EnvConfig = {
    apiBaseUrl: readEnv("NEXT_PUBLIC_API_BASE_URL", "http://localhost:8000/api/v1"),
    wsBaseUrl: readEnv("NEXT_PUBLIC_WS_BASE_URL", "ws://localhost:8001")
};
