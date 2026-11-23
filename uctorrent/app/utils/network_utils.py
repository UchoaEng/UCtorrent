from __future__ import annotations

import socket


def is_port_available(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.2)
        return sock.connect_ex((host, port)) != 0


def find_available_port(host: str, preferred_port: int, attempts: int = 50) -> int:
    for port in range(preferred_port, preferred_port + attempts):
        if is_port_available(host, port):
            return port
    raise OSError(f"Nenhuma porta livre encontrada entre {preferred_port} e {preferred_port + attempts - 1}.")
