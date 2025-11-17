"""
Configuration Manager Module
============================
Module สำหรับจัดการ Configuration ของระบบ Revenue ETL
รองรับการโหลด config จาก JSON file และจัดการ paths ตาม OS

Author: Revenue ETL System
Version: 1.0.0
"""

import json
import os
import platform
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import copy
import calendar


class ConfigManager:
    """
    Configuration Manager สำหรับระบบ Revenue ETL
    จัดการการโหลด config จากไฟล์ภายนอกและปรับแต่งตาม environment
    """
    
    def __init__(self, config_path: str = "config.json"):
        """
        Initialize ConfigManager
        
        Args:
            config_path: path ของไฟล์ configuration (default: config.json)
        """
        self.config_path = config_path
        self.config = None
        self.paths = None
        self.os_platform = platform.system().lower()
        
        # โหลด configuration
        self.load_config()
        
    def load_config(self) -> Dict[str, Any]:
        """
        โหลด configuration จากไฟล์ JSON
        
        Returns:
            dict: configuration ทั้งหมด
            
        Raises:
            FileNotFoundError: เมื่อไม่พบไฟล์ config
            json.JSONDecodeError: เมื่อไฟล์ JSON format ไม่ถูกต้อง
        """
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
                
            # ตั้งค่า paths ตาม OS
            self._setup_paths()
            
            # Validate configuration
            self._validate_config()
            
            print(f"✓ โหลด Configuration จาก {self.config_path} สำเร็จ")
            return self.config
            
        except FileNotFoundError:
            raise FileNotFoundError(f"ไม่พบไฟล์ configuration: {self.config_path}")
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(f"ไฟล์ configuration มีรูปแบบไม่ถูกต้อง: {e}", e.doc, e.pos)
    
    def _setup_paths(self) -> None:
        """
        ตั้งค่า paths ตาม OS ที่ใช้งาน
        """
        # ตรวจสอบว่ามี path configuration สำหรับ OS นี้หรือไม่
        if self.os_platform not in self.config['paths']:
            raise ValueError(f"ไม่รองรับระบบปฏิบัติการ: {self.os_platform}")
        
        os_paths = self.config['paths'][self.os_platform]
        year = self.config['processing_year']
        
        self.paths = {
            # FI Module Paths
            'fi': {
                'base': os_paths['base_path'],
                'master': os_paths['master_path'],
                'input': os.path.join(
                    os_paths['base_path'],
                    year,
                    self.config['fi_module']['input_subpath']
                ),
                'output': os.path.join(
                    os_paths['base_path'],
                    year,
                    self.config['fi_module']['output_subpath']
                ),
                'master_source': os.path.join(
                    os_paths['master_path'],
                    self.config['fi_module']['master_subpath']
                )
            },
            
            # ETL Module Paths
            'etl': {
                'base': os_paths['base_path'],
                'master': os_paths['master_path'],
                'input': os.path.join(
                    os_paths['base_path'],
                    year,
                    self.config['etl_module']['input_subpath']
                ),
                'output': os.path.join(
                    os_paths['base_path'],
                    year,
                    self.config['etl_module']['output_subpath']
                ),
                'final_output': os.path.join(
                    os_paths['base_path'],
                    self.config['etl_module']['final_output_subpath'],
                    year
                )
            }
        }
    
    def _validate_config(self) -> None:
        """
        ตรวจสอบความถูกต้องของ configuration
        
        Raises:
            ValueError: เมื่อ configuration ไม่ครบถ้วนหรือไม่ถูกต้อง
        """
        required_sections = ['environment', 'paths', 'processing_year', 'fi_module', 'etl_module']
        
        for section in required_sections:
            if section not in self.config:
                raise ValueError(f"ขาด configuration section: {section}")
        
        # ตรวจสอบ year format
        year = self.config['processing_year']
        if not year.isdigit() or len(year) != 4:
            raise ValueError(f"processing_year ต้องเป็นตัวเลข 4 หลัก: {year}")
        
        print(f"✓ Configuration validation ผ่าน")

    def _get_last_day_of_month(self, year: int, month: int) -> int:
        """
        คำนวณวันสุดท้ายของเดือน

        Args:
            year: ปี (int)
            month: เดือน (int 1-12)

        Returns:
            int: วันสุดท้ายของเดือน (28-31)
        """
        return calendar.monthrange(year, month)[1]

    def _expand_filename_template(self, template: str, year: str, month: int) -> str:
        """
        แทนที่ placeholders ในชื่อไฟล์ด้วยค่าจริง

        Placeholders:
            {YYYY} - ปี 4 หลัก (เช่น 2025)
            {MM} - เดือน 2 หลัก (เช่น 01, 10)
            {YYYYMM} - ปีเดือน (เช่น 202501)
            {YYYYMMDD} - ปีเดือนวัน (วันสุดท้ายของเดือน) (เช่น 20250131)
            {FI_MONTH} - เดือน 2 หลัก (สำหรับ reconciliation)

        Args:
            template: ชื่อไฟล์ที่มี placeholders
            year: ปี (string)
            month: เดือน (int 1-12)

        Returns:
            str: ชื่อไฟล์ที่แทนที่แล้ว
        """
        if not isinstance(template, str):
            return template

        # แปลง year เป็น int
        year_int = int(year)

        # คำนวณวันสุดท้ายของเดือน
        last_day = self._get_last_day_of_month(year_int, month)

        # แทนที่ placeholders
        result = template
        result = result.replace("{YYYY}", year)
        result = result.replace("{MM}", f"{month:02d}")
        result = result.replace("{YYYYMM}", f"{year}{month:02d}")
        result = result.replace("{YYYYMMDD}", f"{year}{month:02d}{last_day:02d}")
        result = result.replace("{FI_MONTH}", f"{month:02d}")

        return result

    def _expand_dict_templates(self, data: Any, year: str, month: int) -> Any:
        """
        แทนที่ templates ใน dict/list/str แบบ recursive

        Args:
            data: ข้อมูลที่ต้องการแทนที่ (dict, list, str, or other)
            year: ปี
            month: เดือน

        Returns:
            ข้อมูลที่แทนที่แล้ว
        """
        if isinstance(data, dict):
            return {k: self._expand_dict_templates(v, year, month) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._expand_dict_templates(item, year, month) for item in data]
        elif isinstance(data, str):
            return self._expand_filename_template(data, year, month)
        else:
            return data

    def get_fi_config(self) -> Dict[str, Any]:
        """
        ดึง configuration สำหรับ FI Module

        Returns:
            dict: FI module configuration พร้อม paths (ชื่อไฟล์ expand แล้ว)
        """
        fi_config = copy.deepcopy(self.config['fi_module'])
        fi_config['paths'] = self.paths['fi']
        fi_config['year'] = self.config['processing_year']

        # Expand templates สำหรับ FI module
        year = self.config['processing_year']
        fi_month = self.config['processing_months']['fi_current_month']

        # Expand input_files และ output_files
        fi_config['input_files'] = self._expand_dict_templates(
            fi_config['input_files'], year, fi_month
        )
        fi_config['output_files'] = self._expand_dict_templates(
            fi_config['output_files'], year, fi_month
        )

        # เพิ่ม month เข้าไปใน config สำหรับใช้งาน
        fi_config['current_month'] = fi_month

        return fi_config
    
    def get_etl_config(self) -> Dict[str, Any]:
        """
        ดึง configuration สำหรับ ETL Module

        Returns:
            dict: ETL module configuration พร้อม paths (ชื่อไฟล์ expand แล้ว)
        """
        etl_config = copy.deepcopy(self.config['etl_module'])
        etl_config['paths'] = self.paths['etl']
        etl_config['year'] = self.config['processing_year']

        # Expand templates สำหรับ ETL module
        year = self.config['processing_year']
        etl_end_month = self.config['processing_months']['etl_end_month']
        fi_month = self.config['processing_months']['fi_current_month']

        # Expand reconciliation.fi_month
        if 'reconciliation' in etl_config:
            etl_config['reconciliation'] = self._expand_dict_templates(
                etl_config['reconciliation'], year, fi_month
            )

        # เพิ่ม month เข้าไปใน config สำหรับใช้งาน
        etl_config['end_month'] = etl_end_month
        etl_config['fi_month'] = fi_month

        return etl_config
    
    def get_reconciliation_config(self) -> Dict[str, Any]:
        """
        ดึง configuration สำหรับ Reconciliation
        
        Returns:
            dict: Reconciliation configuration
        """
        return self.config['etl_module']['reconciliation']
    
    def update_config(self, section: str, key: str, value: Any) -> None:
        """
        อัพเดท configuration value
        
        Args:
            section: ชื่อ section ใน config
            key: ชื่อ key ที่ต้องการแก้ไข
            value: ค่าใหม่
        """
        if section in self.config and isinstance(self.config[section], dict):
            self.config[section][key] = value
            print(f"✓ อัพเดท config: {section}.{key} = {value}")
        else:
            raise ValueError(f"ไม่พบ section '{section}' ใน configuration")
    
    def save_config(self, backup: bool = True) -> None:
        """
        บันทึก configuration กลับไปยังไฟล์
        
        Args:
            backup: สร้าง backup ของไฟล์เดิมหรือไม่
        """
        # สร้าง backup ถ้าต้องการ
        if backup and os.path.exists(self.config_path):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"{self.config_path}.backup_{timestamp}"
            os.rename(self.config_path, backup_path)
            print(f"✓ สร้าง backup: {backup_path}")
        
        # บันทึกไฟล์ใหม่
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
        
        print(f"✓ บันทึก configuration: {self.config_path}")
    
    def create_directories(self) -> None:
        """
        สร้าง directories ที่จำเป็นสำหรับระบบ
        """
        directories = [
            self.paths['fi']['output'],
            self.paths['etl']['output'],
            self.paths['etl']['final_output']
        ]
        
        # เพิ่ม log directory ถ้าเปิดใช้งาน
        if self.config.get('logging', {}).get('enable_file_logging'):
            log_dir = self.config['logging'].get('log_directory', 'logs')
            directories.append(log_dir)
            directories.append(os.path.join(self.paths['etl']['output'], 'reconcile_logs'))
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
            print(f"✓ สร้าง/ตรวจสอบ directory: {directory}")
    
    def print_config_summary(self) -> None:
        """
        แสดงสรุป configuration ปัจจุบัน
        """
        print("\n" + "=" * 80)
        print("CONFIGURATION SUMMARY")
        print("=" * 80)
        
        print(f"Environment: {self.config['environment']['name']}")
        print(f"Processing Year: {self.config['processing_year']}")
        print(f"Operating System: {self.os_platform}")
        
        print("\nFI Module:")
        print(f"  Input Path: {self.paths['fi']['input']}")
        print(f"  Output Path: {self.paths['fi']['output']}")
        print(f"  Input Files: {self.config['fi_module']['input_files']}")
        
        print("\nETL Module:")
        print(f"  Input Path: {self.paths['etl']['input']}")
        print(f"  Output Path: {self.paths['etl']['output']}")
        print(f"  Final Output: {self.paths['etl']['final_output']}")
        print(f"  Reconciliation: {'Enabled' if self.config['etl_module']['reconciliation']['enabled'] else 'Disabled'}")
        
        print("\nMaster Files:")
        print(f"  Master Path: {self.paths['fi']['master']}")
        
        print("=" * 80)
    
    def get_all_paths(self) -> Dict[str, Any]:
        """
        ดึง paths ทั้งหมด
        
        Returns:
            dict: paths ทั้งหมดของระบบ
        """
        return self.paths
    
    def get_year(self) -> str:
        """
        ดึงปีที่ประมวลผล

        Returns:
            str: ปีที่ประมวลผล
        """
        return self.config['processing_year']

    def set_processing_month(self, month: int, update_etl: bool = True) -> None:
        """
        กำหนดเดือนที่ต้องการประมวลผล (runtime override)

        Args:
            month: เดือนที่ต้องการประมวลผล (1-12)
            update_etl: อัพเดท etl_end_month ด้วยหรือไม่ (default: True)
        """
        if not 1 <= month <= 12:
            raise ValueError(f"เดือนต้องอยู่ระหว่าง 1-12: {month}")

        self.config['processing_months']['fi_current_month'] = month

        if update_etl:
            self.config['processing_months']['etl_end_month'] = month

        print(f"✓ อัพเดทเดือนสำหรับประมวลผล: {month:02d}")

    def get_processing_months(self) -> Dict[str, int]:
        """
        ดึงข้อมูลเดือนที่กำลังประมวลผล

        Returns:
            dict: {'fi_current_month': int, 'etl_end_month': int}
        """
        return self.config['processing_months']


# สร้าง instance สำหรับใช้งานร่วมกัน
_config_manager_instance = None

def get_config_manager(config_path: str = "config.json") -> ConfigManager:
    """
    Factory function สำหรับดึง ConfigManager instance
    ใช้ Singleton pattern เพื่อให้มี instance เดียวทั้งระบบ
    
    Args:
        config_path: path ของไฟล์ configuration
        
    Returns:
        ConfigManager: instance ของ ConfigManager
    """
    global _config_manager_instance
    
    if _config_manager_instance is None:
        _config_manager_instance = ConfigManager(config_path)
    
    return _config_manager_instance


if __name__ == "__main__":
    # ทดสอบ ConfigManager
    try:
        cm = ConfigManager("config.json")
        cm.print_config_summary()
        
        # ทดสอบดึง config แต่ละส่วน
        print("\n\nทดสอบดึง FI Config:")
        fi_config = cm.get_fi_config()
        print(f"FI Input Files: {fi_config['input_files']}")
        
        print("\nทดสอบดึง ETL Config:")
        etl_config = cm.get_etl_config()
        print(f"ETL Reconciliation Enabled: {etl_config['reconciliation']['enabled']}")
        
    except Exception as e:
        print(f"Error: {e}")