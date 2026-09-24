from fastapi import Request
from slowapi import Limiter


def get_client_id(request: Request) -> str:
    client_id = request.headers.get("X-Client-ID")
    if client_id:
        return client_id
    if request.client:
        return request.client.host
    return "127.0.0.1"

limiter = Limiter(key_func=get_client_id)
