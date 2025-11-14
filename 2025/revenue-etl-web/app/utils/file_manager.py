"""
File Manager สำหรับจัดการ report files
"""

import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class FileManager:
    """
    จัดการ report files
    """
    
    def __init__(self, config_manager):
        """
        Args:
            config_manager: ConfigManager instance
        """
        self.config_manager = config_manager
        self.etl_config = config_manager.get_etl_config()
    
    def get_report_directories(self) -> List[str]:
        """
        ดึง list ของ directories ที่เก็บ reports
        
        Returns:
            List of directory paths
        """
        dirs = []
        
        # จาก config
        output_path = self.etl_config.get("output_path")
        report_path = self.etl_config.get("report_path")
        
        if output_path:
            dirs.append(output_path)
        
        if report_path and report_path != output_path:
            dirs.append(report_path)
        
        return dirs
    
    def list_reports(self, year: str = None, month: str = None, 
                    limit: int = 50) -> List[Dict[str, Any]]:
        """
        List available reports
        
        Args:
            year: Filter by year (optional)
            month: Filter by month (optional)
            limit: Maximum number of files to return
        
        Returns:
            List of report file info (sorted by newest first)
        """
        reports = []
        
        for dir_path in self.get_report_directories():
            path = Path(dir_path)
            
            if not path.exists():
                logger.warning(f"Report directory not found: {dir_path}")
                continue
            
            # หาไฟล์ Excel
            for file in path.glob("*.xlsx"):
                try:
                    stat = file.stat()
                    
                    # Parse year/month จาก filename
                    file_year, file_month = self._parse_period_from_filename(file.name)
                    
                    # Filter by year/month
                    if year and file_year != year:
                        continue
                    if month and file_month != month:
                        continue
                    
                    reports.append({
                        "filename": file.name,
                        "path": str(file),
                        "size": stat.st_size,
                        "size_mb": round(stat.st_size / (1024 * 1024), 2),
                        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        "modified_timestamp": stat.st_mtime,
                        "year": file_year,
                        "month": file_month
                    })
                
                except Exception as e:
                    logger.error(f"Error processing file {file}: {e}")
        
        # เรียงตาม modified time (ใหม่ก่อน)
        reports.sort(key=lambda x: x["modified_timestamp"], reverse=True)
        
        # Limit
        return reports[:limit]
    
    def get_report_by_filename(self, filename: str) -> Dict[str, Any]:
        """
        ดึงข้อมูล report โดยใช้ filename
        
        Args:
            filename: Report filename
        
        Returns:
            Report info หรือ None ถ้าไม่พบ
        """
        for dir_path in self.get_report_directories():
            path = Path(dir_path) / filename
            
            if path.exists() and path.is_file():
                try:
                    stat = path.stat()
                    file_year, file_month = self._parse_period_from_filename(filename)
                    
                    return {
                        "filename": filename,
                        "path": str(path),
                        "size": stat.st_size,
                        "size_mb": round(stat.st_size / (1024 * 1024), 2),
                        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        "year": file_year,
                        "month": file_month
                    }
                
                except Exception as e:
                    logger.error(f"Error getting file info {filename}: {e}")
        
        return None
    
    def _parse_period_from_filename(self, filename: str) -> tuple:
        """
        Parse year/month จาก filename
        
        Args:
            filename: Report filename
        
        Returns:
            (year, month) หรือ (None, None) ถ้า parse ไม่ได้
        """
        import re
        
        # ตัวอย่าง: pl_combined_output_202510.xlsx
        # pattern: YYYYMM
        match = re.search(r'(\d{4})(\d{2})', filename)
        
        if match:
            year = match.group(1)
            month = match.group(2)
            return year, month
        
        return None, None
    
    def get_reports_by_period(self, year: str, month: str = None) -> List[Dict[str, Any]]:
        """
        ดึง reports ตาม period
        
        Args:
            year: Year
            month: Month (optional)
        
        Returns:
            List of report file info
        """
        return self.list_reports(year=year, month=month)
    
    def get_latest_report(self) -> Dict[str, Any]:
        """
        ดึง report ล่าสุด
        
        Returns:
            Report info หรือ None ถ้าไม่มี
        """
        reports = self.list_reports(limit=1)
        return reports[0] if reports else None
    
    def file_exists(self, filename: str) -> bool:
        """
        ตรวจสอบว่าไฟล์มีอยู่หรือไม่
        
        Args:
            filename: Report filename
        
        Returns:
            True if exists, False otherwise
        """
        return self.get_report_by_filename(filename) is not None
    
    def get_file_path(self, filename: str) -> str:
        """
        ดึง full path ของไฟล์
        
        Args:
            filename: Report filename
        
        Returns:
            Full file path หรือ None ถ้าไม่พบ
        """
        report = self.get_report_by_filename(filename)
        return report["path"] if report else None
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        ดึงสถิติของ reports
        
        Returns:
            dict: สถิติต่าง ๆ
        """
        reports = self.list_reports(limit=1000)
        
        if not reports:
            return {
                "total_reports": 0,
                "total_size_mb": 0,
                "years": [],
                "latest_report": None
            }
        
        # คำนวณสถิติ
        total_size = sum(r["size"] for r in reports)
        years = sorted(set(r["year"] for r in reports if r["year"]), reverse=True)
        
        return {
            "total_reports": len(reports),
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "years": years,
            "latest_report": reports[0] if reports else None
        }
