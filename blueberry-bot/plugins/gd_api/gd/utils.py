from typing import Any, TypeVar

__all__ = ["safeInt", "safeBool"]

_A = TypeVar(name="_A")


def safeInt(i: Any, fallback: _A = -1) -> int | _A:
    try:
        return int(i)
    except Exception:
        return fallback


def safeBool(v: Any) -> bool:
    """GD 风格布尔值解析：空或 '0' 为 False，其他为 True。"""
    return bool(v) and v != "0"


if __name__ == "__main__":
    print(safeInt("42"))
    print(safeInt("abc", -1))
    print(safeBool("1"))
    print(safeBool("0"))
    print(safeBool(""))
