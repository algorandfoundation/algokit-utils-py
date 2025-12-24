from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def as_bytes(arr: list[int]) -> bytes:
    return bytes(arr)
