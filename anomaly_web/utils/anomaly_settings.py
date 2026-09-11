DEFAULT_ANOMALY_SETTINGS = {
    "iqr_k": 2.0,
    "min_change_ratio": 0.10,
    "constant_change_ratio": 0.15,
    "peer_contamination": 0.05,
    "peer_zscore_threshold": 2.0,
    "peer_min_group_size": 5,
}


def _is_blank(value):
    return value is None or value == ""


def _float(value, default, minimum=None, maximum=None):
    if _is_blank(value):
        return default
    try:
        value = float(value)
    except (TypeError, ValueError):
        return default
    if minimum is not None:
        value = max(minimum, value)
    if maximum is not None:
        value = min(maximum, value)
    return value


def _ratio(value, default, minimum=0.0, maximum=1.0):
    value = _float(value, default)
    if value > 1:
        value = value / 100
    return max(minimum, min(maximum, value))


def _int(value, default, minimum=None):
    if _is_blank(value):
        return default
    try:
        value = int(value)
    except (TypeError, ValueError):
        return default
    if minimum is not None:
        value = max(minimum, value)
    return value


def normalize_anomaly_settings(config=None):
    config = config or {}
    defaults = DEFAULT_ANOMALY_SETTINGS
    return {
        "iqr_k": _float(config.get("iqr_k"), defaults["iqr_k"], minimum=0.1),
        "min_change_ratio": _ratio(config.get("min_change_ratio"), defaults["min_change_ratio"]),
        "constant_change_ratio": _ratio(config.get("constant_change_ratio"), defaults["constant_change_ratio"]),
        "peer_contamination": _ratio(
            config.get("peer_contamination"),
            defaults["peer_contamination"],
            minimum=0.001,
            maximum=0.5,
        ),
        "peer_zscore_threshold": _float(
            config.get("peer_zscore_threshold"),
            defaults["peer_zscore_threshold"],
            minimum=0.0,
        ),
        "peer_min_group_size": _int(
            config.get("peer_min_group_size"),
            defaults["peer_min_group_size"],
            minimum=2,
        ),
    }
