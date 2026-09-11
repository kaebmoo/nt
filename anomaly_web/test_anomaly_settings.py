"""เช็ค anomaly thresholds: python3 test_anomaly_settings.py"""
import os
import shutil
import tempfile

import pandas as pd

from utils.anomaly_engine import CrosstabGenerator, FullAuditEngine, detect_iqr_anomaly
from utils.anomaly_reporter import ExcelReporter
from utils.config_manager import ConfigManager
from utils.anomaly_settings import normalize_anomaly_settings


def main():
    settings = normalize_anomaly_settings({
        "iqr_k": "3",
        "min_change_ratio": "20",
        "constant_change_ratio": "25",
        "peer_contamination": "20",
        "peer_zscore_threshold": "10",
        "peer_min_group_size": "6",
        "date_grain": "year",
    })
    assert settings["min_change_ratio"] == 0.20
    assert settings["constant_change_ratio"] == 0.25
    assert settings["peer_contamination"] == 0.20
    assert settings["peer_min_group_size"] == 6
    assert settings["date_grain"] == "year"

    row = pd.Series([100, 100, 100, 124])
    assert detect_iqr_anomaly(124, [100, 100, 100], 3)[0] == "Spike_vs_Constant"
    assert detect_iqr_anomaly(124, [100, 100, 100], 3, settings)[0] == "Normal"
    assert CrosstabGenerator(pd.DataFrame(), anomaly_settings=settings)._get_status_helper(row, 3)[0] == "Normal"

    fd, path = tempfile.mkstemp(suffix=".xlsx")
    os.close(fd)
    reporter = ExcelReporter(path, anomaly_settings=settings)
    assert reporter._compute_cell_anomaly(124, [100, 100, 100], 3) == "Normal"
    pd.DataFrame({"ok": [1]}).to_excel(reporter.writer, sheet_name="dummy", index=False)
    reporter.save()
    os.remove(path)

    dates = pd.to_datetime(["2024-01-01", "2024-02-01", "2024-03-01", "2024-04-01"])
    df = pd.DataFrame({
        "GROUP": ["A"] * 4,
        "__date_col__": dates,
        "VALUE": [100, 100, 100, 124],
    })
    default_hits = FullAuditEngine(df).audit_time_series_all_months(
        "VALUE", "__date_col__", ["GROUP"], window=4
    )
    relaxed_hits = FullAuditEngine(df, anomaly_settings=settings).audit_time_series_all_months(
        "VALUE", "__date_col__", ["GROUP"], window=4
    )
    assert "Spike_vs_Constant" in set(default_hits["ISSUE_DESC"])
    assert "Spike_vs_Constant" not in set(relaxed_hits["ISSUE_DESC"])

    tmp = tempfile.mkdtemp()
    cm = ConfigManager(tmp)
    config = {
        "file_id": "wrong",
        "input_mode": "long",
        "date_column": "DATE",
        "target_col": "VALUE",
        "crosstab_dimensions": ["GROUP"],
        "run_time_series_analysis": True,
        "run_peer_group_analysis": False,
        "min_change_ratio": "20",
        "date_grain": "month",
    }
    cm.save_config("right", config.copy())
    assert cm.load_config("right")["file_id"] == "right"
    cm.save_template("T", config.copy())
    template = cm.load_template("T")
    assert "file_id" not in template
    assert template["min_change_ratio"] == 0.20
    assert template["date_grain"] == "month"
    crosstab_only = {
        "input_mode": "crosstab",
        "crosstab_dimensions": ["GROUP"],
        "crosstab_id_vars": ["GROUP"],
        "crosstab_value_name": "AMOUNT",
        "run_crosstab_report": True,
        "run_time_series_analysis": False,
        "run_peer_group_analysis": False,
    }
    assert cm.validate_config(crosstab_only)["valid"]
    assert cm.normalize_config(crosstab_only)["target_col"] == "AMOUNT"
    shutil.rmtree(tmp)

    print("OK")


if __name__ == "__main__":
    main()
