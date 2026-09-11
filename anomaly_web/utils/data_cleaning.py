import re

import pandas as pd


DATE_PARSE_MODES = {
    "auto",
    "dayfirst",
    "monthfirst",
    "ymd",
    "dmy_dot",
    "dmy_slash",
    "mdy_slash",
    "yyyymmdd",
    "excel_serial",
}

DATE_GRAINS = {"day", "month", "year"}
BAD_VALUE_POLICIES = {"zero", "drop", "error"}
BAD_DATE_POLICIES = {"drop", "error", "keep"}


def blank_mask(series):
    text = series.astype("string").str.strip()
    return (
        series.isna()
        | text.isna()
        | text.eq("")
        | text.str.lower().isin(["nan", "none", "null", "na", "n/a", "-"])
    )


def clean_numeric_series(series):
    """Convert accounting-style values to numbers while preserving invalid cells as NaN."""
    if pd.api.types.is_numeric_dtype(series):
        return pd.to_numeric(series, errors="coerce")

    text = series.astype("string").str.strip()
    text = text.str.replace(r"^\((.*)\)$", r"-\1", regex=True)
    text = text.str.replace(r"[,\s$฿%]", "", regex=True)
    text = text.str.replace("\u00a0", "", regex=False)
    return pd.to_numeric(text, errors="coerce")


def numeric_bad_mask(source, numeric):
    return (~blank_mask(source)) & numeric.isna()


def apply_value_transform(series, multiplier=1.0, add=0.0):
    return (series * float(multiplier)) + float(add)


def parse_date_series(series, mode="auto"):
    """Parse dates with Excel/Thai finance friendly defaults."""
    mode = mode if mode in DATE_PARSE_MODES else "auto"

    if pd.api.types.is_datetime64_any_dtype(series):
        return pd.to_datetime(series, errors="coerce")

    if mode == "excel_serial" or (mode == "auto" and _looks_like_excel_serial(series)):
        numeric = pd.to_numeric(series, errors="coerce")
        return pd.to_datetime(numeric, unit="D", origin="1899-12-30", errors="coerce")

    text = series.astype("string").str.strip()

    format_by_mode = {
        "ymd": "%Y-%m-%d",
        "dmy_dot": "%d.%m.%Y",
        "dmy_slash": "%d/%m/%Y",
        "mdy_slash": "%m/%d/%Y",
        "yyyymmdd": "%Y%m%d",
    }
    if mode in format_by_mode:
        return pd.to_datetime(text, format=format_by_mode[mode], errors="coerce")

    if mode == "dayfirst":
        return pd.to_datetime(text, errors="coerce", dayfirst=True)
    if mode == "monthfirst":
        return pd.to_datetime(text, errors="coerce", dayfirst=False)

    for pattern, fmt in [
        (r"\d{1,2}\.\d{1,2}\.\d{4}", "%d.%m.%Y"),
        (r"\d{4}-\d{1,2}-\d{1,2}", "%Y-%m-%d"),
        (r"\d{4}/\d{1,2}/\d{1,2}", "%Y/%m/%d"),
        (r"\d{4}-\d{1,2}", "%Y-%m"),
        (r"\d{4}/\d{1,2}", "%Y/%m"),
        (r"\d{8}", "%Y%m%d"),
        (r"\d{1,2}[A-Za-z]{3}\d{4}", "%d%b%Y"),
        (r"\d{1,2}/\d{1,2}/\d{4}", "%d/%m/%Y"),
    ]:
        if _pattern_ratio(text, pattern) >= 0.6:
            return pd.to_datetime(text, format=fmt, errors="coerce")

    default = pd.to_datetime(text, errors="coerce", dayfirst=False)
    dayfirst = pd.to_datetime(text, errors="coerce", dayfirst=True)
    return dayfirst if dayfirst.notna().sum() > default.notna().sum() else default


def apply_date_grain(series, grain="month"):
    grain = grain if grain in DATE_GRAINS else "month"
    dates = pd.to_datetime(series, errors="coerce")
    if grain == "year":
        return dates.dt.to_period("Y").dt.to_timestamp()
    if grain == "day":
        return dates.dt.floor("D")
    return dates.dt.to_period("M").dt.to_timestamp()


def format_date_label(value, grain="month"):
    grain = grain if grain in DATE_GRAINS else "month"
    try:
        timestamp = pd.Timestamp(value)
    except Exception:
        return str(value)
    if pd.isna(timestamp):
        return ""
    if grain == "year":
        return timestamp.strftime("%Y")
    if grain == "day":
        return timestamp.strftime("%Y-%m-%d")
    return timestamp.strftime("%Y-%m")


def _pattern_ratio(text, pattern):
    sample = text.dropna().head(100)
    if sample.empty:
        return 0
    return sample.str.fullmatch(pattern, flags=re.IGNORECASE).sum() / len(sample)


def _looks_like_excel_serial(series):
    numeric = pd.to_numeric(series, errors="coerce").dropna().head(100)
    if numeric.empty:
        return False
    return numeric.between(20000, 80000).mean() >= 0.8
