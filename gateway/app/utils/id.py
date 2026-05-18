import secrets


def generate_id() -> str:
    return secrets.token_urlsafe(12)
