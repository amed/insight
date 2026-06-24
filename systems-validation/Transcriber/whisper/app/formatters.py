def normalize_probability(value: float | None) -> float:
    if value is None:
        return 0.0
    return float(max(0.0, min(1.0, value)))
