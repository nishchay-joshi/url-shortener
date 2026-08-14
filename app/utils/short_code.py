import secrets


BASE62_ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"


def generate_base62_code(length: int = 8) -> str:
    return "".join(secrets.choice(BASE62_ALPHABET) for _ in range(length))