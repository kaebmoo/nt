"""
Revenue ETL System - Main Program
==================================
โปรแกรมหลักสำหรับประมวลผลข้อมูล Revenue ETL
รองรับการเรียกใช้งานแบบ Command Line และ Web Application

Author: Revenue ETL System
Version: 2.0.0
"""

import sys
import os
import argparse
from datetime import datetime
import traceback
from pathlib import Path

# Import modules
from config_manager import ConfigManager, get_config_manager
from fi_revenue_expense_module import FIRevenueExpenseProcessor

# Import revenue_etl_report (original module with Config class)
# เราจะ import และแก้ไข Config ให้ใช้จาก ConfigManager แทน
import revenue_etl_report


class RevenueETLSystem:
    """
    ระบบ Revenue ETL หลัก
    จัดการการประมวลผลตามลำดับและ dependencies
    """
    
    def __init__(self, config_path: str = "config.json"):
        """
        Initialize Revenue ETL System
        
        Args:
            config_path: path ของไฟล์ configuration
        """
        self.config_manager = get_config_manager(config_path)
        self.fi_processor = None
        self.etl_processor = None
        
        # สถานะการประมวลผล
        self.fi_completed = False
        self.etl_completed = False
        
        # ผลลัพธ์
        self.fi_output = None
        self.etl_output = None
        
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
            
            # สร้าง processor
            self.fi_processor = FIRevenueExpenseProcessor(fi_config)
            
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
            etl_config = self.config_manager.get_etl_config()

            # สร้าง ETL instance (V2 - ส่ง config dict และ paths เข้าไปโดยตรง)
            self.etl_processor = revenue_etl_report.RevenueETL(
                config=etl_config,
                paths=etl_config['paths']
            )

            # รัน ETL Pipeline (รวม reconciliation, mapping, และ anomaly detection)
            self.log("กำลังรัน ETL Pipeline...")
            df_result, anomaly_results = self.etl_processor.run()

            if df_result is not None:
                self.etl_completed = True
                self.etl_output = {
                    'df_result': df_result,
                    'anomaly_results': anomaly_results
                }

                self.log("✓ ETL Pipeline ประมวลผลสำเร็จ", "SUCCESS")

                # สร้าง Excel Report
                self.log("\n" + "=" * 100)
                self.log("STEP 3: Creating Excel Report")
                self.log("=" * 100)

                excel_file = self.etl_processor.create_excel_report(df_result, anomaly_results)
                self.log(f"✓ Excel Report สร้างเสร็จสมบูรณ์: {excel_file}", "SUCCESS")

                return True
            else:
                self.log("❌ ETL Module ประมวลผลล้มเหลว", "ERROR")
                return False

        except Exception as e:
            self.log(f"❌ เกิดข้อผิดพลาดในการรัน ETL Module: {e}", "ERROR")
            traceback.print_exc()
            return False

    def run_all(self) -> bool:
        """
        รันระบบทั้งหมดตามลำดับ
        
        Returns:
            bool: True ถ้าสำเร็จทั้งหมด, False ถ้ามีข้อผิดพลาด
        """
        start_time = datetime.now()
        
        self.log("=" * 100)
        self.log("REVENUE ETL SYSTEM - เริ่มประมวลผล")
        self.log("=" * 100)
        
        # แสดง configuration summary
        self.config_manager.print_config_summary()
        
        # สร้าง directories
        self.log("\nสร้าง/ตรวจสอบ Directories...")
        self.config_manager.create_directories()
        
        # รัน FI Module
        if not self.run_fi_module():
            self.log("❌ ระบบหยุดทำงานเนื่องจาก FI Module ล้มเหลว", "ERROR")
            return False
        
        # รัน ETL Module
        if not self.run_etl_module():
            self.log("❌ ระบบหยุดทำงานเนื่องจาก ETL Module ล้มเหลว", "ERROR")
            return False
        
        # สรุปผล
        end_time = datetime.now()
        duration = end_time - start_time
        
        self.log("\n" + "=" * 100)
        self.log("สรุปผลการประมวลผล")
        self.log("=" * 100)
        self.log(f"สถานะ: {'สำเร็จ' if (self.fi_completed and self.etl_completed) else 'ล้มเหลว'}")
        self.log(f"FI Module: {'✓ สำเร็จ' if self.fi_completed else '✗ ล้มเหลว'}")
        self.log(f"ETL Module: {'✓ สำเร็จ' if self.etl_completed else '✗ ล้มเหลว'}")
        self.log(f"เวลาที่ใช้: {duration}")
        self.log("=" * 100)
        
        return self.fi_completed and self.etl_completed


def main():
    """
    Main function สำหรับ command line interface
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
        choices=['all', 'fi', 'etl'],
        default='all',
        help='เลือก module ที่ต้องการรัน (default: all)'
    )
    
    parser.add_argument(
        '--update-config',
        action='store_true',
        help='เปิดโหมดแก้ไข configuration'
    )
    
    parser.add_argument(
        '--year',
        type=str,
        help='กำหนดปีที่ต้องการประมวลผล (override config)'
    )
    
    args = parser.parse_args()
    
    try:
        # สร้าง system instance
        system = RevenueETLSystem(args.config)
        
        # อัพเดท config ถ้ามีการระบุ
        if args.year:
            system.config_manager.update_config('processing_year', '', args.year)
            system.log(f"อัพเดทปีเป็น: {args.year}")
        
        # โหมดแก้ไข config
        if args.update_config:
            system.log("เปิดโหมดแก้ไข Configuration")
            # TODO: implement interactive config editor
            system.log("(ฟีเจอร์นี้ยังไม่พร้อมใช้งาน)")
            return
        
        # รัน module ตามที่เลือก
        success = False
        
        if args.module == 'all':
            success = system.run_all()
        elif args.module == 'fi':
            success = system.run_fi_module()
        elif args.module == 'etl':
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