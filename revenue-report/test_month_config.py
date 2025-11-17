#!/usr/bin/env python3
"""
Test Script for Month Configuration
ทดสอบการทำงานของ month configuration system
"""

import os
import sys
from config_manager import ConfigManager

def test_config_manager():
    """ทดสอบ ConfigManager"""
    print("=" * 80)
    print("ทดสอบ ConfigManager - Template Expansion")
    print("=" * 80)

    # Load config
    cm = ConfigManager("config.json")

    # แสดง processing_months
    months = cm.get_processing_months()
    print(f"\n📅 Processing Months:")
    print(f"  FI Current Month: {months['fi_current_month']:02d}")
    print(f"  ETL End Month: {months['etl_end_month']:02d}")

    # ทดสอบ FI Config
    print("\n" + "=" * 80)
    print("FI Module Configuration")
    print("=" * 80)
    fi_config = cm.get_fi_config()
    print(f"\nYear: {fi_config['year']}")
    print(f"Current Month: {fi_config['current_month']:02d}")
    print(f"\nInput Files:")
    for f in fi_config['input_files']:
        print(f"  - {f}")
    print(f"\nOutput Files:")
    for key, f in fi_config['output_files'].items():
        print(f"  - {key}: {f}")

    # ทดสอบ ETL Config
    print("\n" + "=" * 80)
    print("ETL Module Configuration")
    print("=" * 80)
    etl_config = cm.get_etl_config()
    print(f"\nYear: {etl_config['year']}")
    print(f"End Month: {etl_config['end_month']:02d}")
    print(f"FI Month: {etl_config['fi_month']:02d}")
    print(f"\nReconciliation:")
    print(f"  Enabled: {etl_config['reconciliation']['enabled']}")
    print(f"  FI Month: {etl_config['reconciliation']['fi_month']}")
    print(f"  Tolerance: {etl_config['reconciliation']['tolerance']}")

    # ทดสอบ set_processing_month
    print("\n" + "=" * 80)
    print("ทดสอบ Override Month")
    print("=" * 80)
    print("\n🔄 Override เดือนเป็น 5...")
    cm.set_processing_month(5)

    # Reload config
    fi_config = cm.get_fi_config()
    etl_config = cm.get_etl_config()

    print(f"\nหลัง Override:")
    print(f"  FI Input Files: {fi_config['input_files']}")
    print(f"  FI Output Files (Excel): {fi_config['output_files']['excel']}")
    print(f"  ETL End Month: {etl_config['end_month']:02d}")
    print(f"  Reconciliation FI Month: {etl_config['reconciliation']['fi_month']}")

    print("\n" + "=" * 80)
    print("✅ ทดสอบเสร็จสมบูรณ์")
    print("=" * 80)

if __name__ == "__main__":
    try:
        test_config_manager()
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาด: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
