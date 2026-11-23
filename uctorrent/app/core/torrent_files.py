from __future__ import annotations


PRIORITIES = {
    0: "Nao baixar",
    1: "Baixa",
    4: "Normal",
    6: "Alta",
    7: "Maxima",
}


def wanted_from_priority(priority: int) -> bool:
    return priority > 0

