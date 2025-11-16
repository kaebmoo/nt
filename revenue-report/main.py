"""
Revenue ETL System - Main Program
==================================
โปรแกรมหลักสำหรับประมวลผลข้อมูล Revenue ETL (V2.1)
- ใช้ ConfigManager
- เรียก FI Module (V2)
- เรียก ETL Module (V2) (ซึ่งมี Reconciliation ภายใน)
- เรียก Excel Report Function (V2)

Author: Revenue ETL System
Version: 2.1.0
"""

import sys
import os
import argparse
from datetime import datetime
import traceback
from pathlib import Path

# Import V2 modules
from config_manager import ConfigManager, get_config_manager
from fi_revenue_expense_module import FIRevenueExpenseProcessor

# Import revenue_etl_report module เพื่อสร้าง RevenueETL instance
import revenue_etl_report


class RevenueETLSystem:
    """
    ระบบ Revenue ETL หลัก (V2.1)
    Class นี้ถูกเรียกใช้โดย main() (สำหรับ CLI)
    และถูกเรียกใช้โดย web_app.py (สำหรับ UI)
    """
    
    def __init__(self, config_path: str = "config.json"):
        """
        Initialize Revenue ETL System
        
        Args:
            config_path: path ของไฟล์ configuration
        """
        self.config_manager = get_config_manager(config_path)
        
        # ดึง config ที่อัพเดท path แล้ว
        self.fi_config = self.config_manager.get_fi_config()
        self.etl_config = self.config_manager.get_etl_config()
        
        self.fi_processor = None
        self.etl_processor = None
        
        # สถานะการประมวลผล (สำหรับ web_app)
        self.fi_completed = False
        self.etl_completed = False
        
        # ผลลัพธ์
        self.fi_output = None
        self.etl_final_df = None
        self.etl_anomaly_results = None
        
    def log(self, message: str, level: str = "INFO") -> None:
        """
        แสดงข้อความ log
        
        Args:
            message: ข้อความที่ต้องการแสดง
            level: ระดับของ log
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
    
    def run_fi_module(self) -> bool:
        """
        รัน FI Revenue Expense Module
        
        Returns:
            bool: True ถ้าสำเร็จ, False ถ้าล้มเหลว
        """
        try:
            self.log("=" * 100)
            self.log("STEP 1: FI Revenue Expense Processing")
            self.log("=" * 100)
            
            # ดึง config สำหรับ FI module
            fi_config = self.config_manager.get_fi_config()
            self.fi_processor = FIRevenueExpenseProcessor(self.fi_config)
            
            # สร้าง processor
            # รันการประมวลผล
            if self.fi_processor.run():
                self.fi_completed = True
                self.fi_output = self.fi_processor.get_output_files()
                
                self.log("✓ FI Module ประมวลผลสำเร็จ", "SUCCESS")
                self.log(f"  Output Files:")
                for key, path in self.fi_output.items():
                    self.log(f"    - {key}: {path}")
                
                return True
            else:
                self.log("❌ FI Module ประมวลผลล้มเหลว", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ เกิดข้อผิดพลาดในการรัน FI Module: {e}", "ERROR")
            traceback.print_exc()
            return False
    
    def run_etl_module(self) -> bool:
        """
        รัน Revenue ETL Module

        Returns:
            bool: True ถ้าสำเร็จ, False ถ้าล้มเหลว
        (*** แก้ไข ***)
        รัน Revenue ETL Module (V2) และสร้าง Excel Report ต่อทันที
        """
        try:
            self.log("\n" + "=" * 100)
            self.log("STEP 2: Revenue ETL Pipeline Processing")
            self.log("=" * 100)

            # ตรวจสอบว่า FI module ทำงานเสร็จแล้ว
            if not self.fi_completed:
                self.log("⚠️ FI Module ยังไม่ได้ประมวลผล กำลังรัน FI Module ก่อน...", "WARNING")
                if not self.run_fi_module():
                    self.log("❌ ไม่สามารถรัน ETL Module เนื่องจาก FI Module ล้มเหลว", "ERROR")
                    return False
            # ดึง config สำหรับ ETL module
            # สร้าง ETL instance (V2 - ส่ง config dict และ paths เข้าไปโดยตรง)
            
            # 1. สร้าง ETL instance (V2) โดย "ฉีด" config เข้าไป
            # (คง "Hack" เดิมไว้ เพื่อให้ Reconciler (V1 logic) หาไฟล์ FI เจอ)
            full_etl_config = self.etl_config.copy()
            fi_output_path = self.fi_config['paths']['output']
            fi_csv_revenue = self.fi_config['output_files']['csv_revenue']
            
            # สร้าง path ที่ V1 reconcile logic คาดหวัง
            # full_etl_config['v1_hack_fi_path'] = os.path.join(
            #     fi_output_path, fi_csv_revenue
            # )
            # มันสร้างมาทำไมวะ ไม่ได้ใช้?
            
            self.etl_processor = revenue_etl_report.RevenueETL(
                config=full_etl_config, 
                paths=self.etl_config['paths']
            )
            
            # 2. รัน ETL Pipeline (step 1-5, รวม reconciliation)
            df_result, anomaly_results = self.etl_processor.run()
            
            if df_result is None:
                self.log("❌ ETL Module ประมวลผลล้มเหลว (run()ล้มเหลว)", "ERROR")
                return False

            self.etl_final_df = df_result
            self.etl_anomaly_results = anomaly_results
            self.log("✓ ETL Pipeline (CSV) ประมวลผลสำเร็จ", "SUCCESS")

            # 3. สร้าง Excel Report ต่อทันที
            # (นี่คือสิ่งที่ web_app.py คาดหวัง)
            self.log("\n" + "=" * 100)
            self.log("STEP 3: Creating Final Excel Report")
            self.log("=" * 100)

            # เรียก method create_excel_report จาก etl_processor object
            excel_path = self.etl_processor.create_excel_report(
                self.etl_final_df,
                self.etl_anomaly_results
            )

            self.log(f"✓ Final Excel Report สร้างสำเร็จ: {excel_path}", "SUCCESS")
            self.etl_completed = True
            return True
                
        except Exception as e:
            self.log(f"❌ เกิดข้อผิดพลาดในการรัน ETL Module: {e}", "ERROR")
            traceback.print_exc()
            return False

    def run_all(self) -> bool:
        """
        รันระบบทั้งหมดตามลำดับ
        
        Returns:
            bool: True ถ้าสำเร็จทั้งหมด, False ถ้ามีข้อผิดพลาด
        (คง comment และ log เดิมไว้)
        """
        start_time = datetime.now()
        
        self.log("=" * 100)
        self.log("=" * 100)
        
        self.config_manager.print_config_summary()
        
        self.log("\nสร้าง/ตรวจสอบ Directories...")
        self.config_manager.create_directories()
        
        # 1. รัน FI
        if not self.run_fi_module():
            self.log("❌ ระบบหยุดทำงานเนื่องจาก FI Module ล้มเหลว", "ERROR")
            return False
        
        # 2. รัน ETL (ซึ่งตอนนี้รวมการสร้าง Report แล้ว)
        if not self.run_etl_module():
            self.log("❌ ระบบหยุดทำงานเนื่องจาก ETL Module ล้มเหลว", "ERROR")
            return False
        
        # สรุปผล
        end_time = datetime.now()
        duration = end_time - start_time
        
        self.log("\n" + "=" * 100)
        self.log("สรุปผลการประมวลผล")
        self.log("=" * 100)
        self.log(f"สถานะ: สำเร็จ")
        self.log(f"FI Module: ✓ สำเร็จ")
        self.log(f"ETL Module: ✓ สำเร็จ (รวม Excel Report)")
        self.log(f"เวลาที่ใช้: {duration}")
        self.log("=" * 100)
        
        return True


def main():
    """
    Main function สำหรับ command line interface
    (สอดคล้องกับ run.sh)
    (คง comment และ log เดิมไว้)
    """
    parser = argparse.ArgumentParser(
        description='Revenue ETL System - ระบบประมวลผลข้อมูลรายได้'
    )
    
    parser.add_argument(
        '--config',
        type=str,
        default='config.json',
        help='Path ของไฟล์ configuration (default: config.json)'
    )
    
    parser.add_argument(
        '--module',
        type=str,
        choices=['all', 'fi', 'etl'], # (ลบ 'report' ที่ซ้ำซ้อนออก)
        default='all',
        help='เลือก module ที่ต้องการรัน (default: all)'
    )
    
    parser.add_argument(
        '--year',
        type=str,
        help='กำหนดปีที่ต้องการประมวลผล (override config - ยังไม่รองรับเต็มรูปแบบ)'
    )
    
    args = parser.parse_args()
    
    try:
        # สร้าง system instance
        system = RevenueETLSystem(args.config)
        
        if args.year:
            system.log(f"การ Override ปี ({args.year}) ยังไม่รองรับเต็มรูปแบบ", "WARNING")
        
        # รัน module ตามที่เลือก
        success = False
        
        if args.module == 'all':
            success = system.run_all()
        elif args.module == 'fi':
            success = system.run_fi_module()
        elif args.module == 'etl':
            # รัน ETL (ซึ่งจะบังคับรัน FI ก่อน และสร้าง report ในตัว)
            success = system.run_etl_module()
        
        # Exit code
        sys.exit(0 if success else 1)
        
    except FileNotFoundError as e:
        print(f"❌ ไม่พบไฟล์: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาด: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()