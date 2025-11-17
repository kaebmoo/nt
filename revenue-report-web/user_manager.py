"""
User Manager Module
===================
จัดการผู้ใช้งานผ่าน JSON file (ไม่ใช้ database)
รองรับ CRUD operations
"""

import json
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path


class UserManager:
    """จัดการข้อมูลผู้ใช้"""

    def __init__(self, users_file: str = "data/users.json"):
        """
        Initialize UserManager

        Args:
            users_file: path ของไฟล์ users.json
        """
        self.users_file = users_file
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        """ตรวจสอบว่าไฟล์ users.json มีอยู่ ถ้าไม่มีให้สร้างใหม่"""
        if not Path(self.users_file).exists():
            # สร้างไฟล์เปล่า
            self._save_users({"users": []})

    def _load_users(self) -> Dict[str, List[Dict[str, Any]]]:
        """โหลดข้อมูลผู้ใช้จากไฟล์"""
        try:
            with open(self.users_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data
        except (FileNotFoundError, json.JSONDecodeError):
            return {"users": []}

    def _save_users(self, data: Dict[str, List[Dict[str, Any]]]) -> bool:
        """บันทึกข้อมูลผู้ใช้ลงไฟล์"""
        try:
            with open(self.users_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving users: {e}")
            return False

    def get_all_users(self) -> List[Dict[str, Any]]:
        """
        ดึงรายชื่อผู้ใช้ทั้งหมด

        Returns:
            List[Dict]: รายชื่อผู้ใช้
        """
        data = self._load_users()
        return data.get('users', [])

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        ค้นหาผู้ใช้จาก email

        Args:
            email: email ของผู้ใช้

        Returns:
            Dict หรือ None ถ้าไม่พบ
        """
        users = self.get_all_users()
        for user in users:
            if user['email'].lower() == email.lower():
                return user
        return None

    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        ค้นหาผู้ใช้จาก ID

        Args:
            user_id: ID ของผู้ใช้

        Returns:
            Dict หรือ None ถ้าไม่พบ
        """
        users = self.get_all_users()
        for user in users:
            if user['id'] == user_id:
                return user
        return None

    def create_user(self, email: str, name: str, is_admin: bool = False) -> Dict[str, Any]:
        """
        สร้างผู้ใช้ใหม่

        Args:
            email: email ของผู้ใช้
            name: ชื่อผู้ใช้
            is_admin: เป็น admin หรือไม่ (default: False)

        Returns:
            Dict: ข้อมูลผู้ใช้ที่สร้างใหม่

        Raises:
            ValueError: ถ้า email ซ้ำ
        """
        # ตรวจสอบว่า email ซ้ำหรือไม่
        if self.get_user_by_email(email):
            raise ValueError(f"User with email {email} already exists")

        # สร้างผู้ใช้ใหม่
        new_user = {
            "id": str(uuid.uuid4())[:8],  # Short UUID
            "email": email.lower(),
            "name": name,
            "is_admin": is_admin,
            "is_active": True,
            "created_at": datetime.now().isoformat(),
            "last_login": None
        }

        # เพิ่มลงในไฟล์
        data = self._load_users()
        data['users'].append(new_user)
        self._save_users(data)

        return new_user

    def update_user(self, user_id: str, **kwargs) -> bool:
        """
        อัพเดทข้อมูลผู้ใช้

        Args:
            user_id: ID ของผู้ใช้
            **kwargs: ฟิลด์ที่ต้องการอัพเดท (name, is_admin, is_active)

        Returns:
            bool: True ถ้าสำเร็จ
        """
        data = self._load_users()
        users = data['users']

        for i, user in enumerate(users):
            if user['id'] == user_id:
                # อัพเดทเฉพาะฟิลด์ที่อนุญาต
                allowed_fields = ['name', 'is_admin', 'is_active', 'last_login']
                for key, value in kwargs.items():
                    if key in allowed_fields:
                        users[i][key] = value

                data['users'] = users
                return self._save_users(data)

        return False

    def delete_user(self, user_id: str) -> bool:
        """
        ลบผู้ใช้

        Args:
            user_id: ID ของผู้ใช้

        Returns:
            bool: True ถ้าสำเร็จ
        """
        data = self._load_users()
        users = data['users']

        # Filter out the user
        new_users = [user for user in users if user['id'] != user_id]

        if len(new_users) == len(users):
            # ไม่มีการลบเกิดขึ้น (ไม่พบ user)
            return False

        data['users'] = new_users
        return self._save_users(data)

    def update_last_login(self, email: str) -> bool:
        """
        อัพเดทเวลา login ล่าสุด

        Args:
            email: email ของผู้ใช้

        Returns:
            bool: True ถ้าสำเร็จ
        """
        user = self.get_user_by_email(email)
        if user:
            return self.update_user(
                user['id'],
                last_login=datetime.now().isoformat()
            )
        return False

    def is_admin(self, email: str) -> bool:
        """
        ตรวจสอบว่าผู้ใช้เป็น admin หรือไม่

        Args:
            email: email ของผู้ใช้

        Returns:
            bool: True ถ้าเป็น admin
        """
        user = self.get_user_by_email(email)
        if user:
            return user.get('is_admin', False)
        return False

    def is_active(self, email: str) -> bool:
        """
        ตรวจสอบว่าผู้ใช้ active หรือไม่

        Args:
            email: email ของผู้ใช้

        Returns:
            bool: True ถ้า active
        """
        user = self.get_user_by_email(email)
        if user:
            return user.get('is_active', False)
        return False

    def get_active_users(self) -> List[Dict[str, Any]]:
        """
        ดึงรายชื่อผู้ใช้ที่ active เท่านั้น

        Returns:
            List[Dict]: รายชื่อผู้ใช้ที่ active
        """
        users = self.get_all_users()
        return [user for user in users if user.get('is_active', False)]

    def export_users_csv(self, output_file: str = "users_export.csv") -> bool:
        """
        Export ผู้ใช้เป็น CSV

        Args:
            output_file: ชื่อไฟล์ output

        Returns:
            bool: True ถ้าสำเร็จ
        """
        try:
            import csv

            users = self.get_all_users()

            with open(output_file, 'w', newline='', encoding='utf-8') as f:
                if users:
                    fieldnames = users[0].keys()
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(users)

            return True
        except Exception as e:
            print(f"Error exporting users: {e}")
            return False

    def import_users_csv(self, input_file: str) -> int:
        """
        Import ผู้ใช้จาก CSV

        Args:
            input_file: ชื่อไฟล์ input

        Returns:
            int: จำนวนผู้ใช้ที่ import สำเร็จ
        """
        try:
            import csv

            count = 0
            with open(input_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        # ตรวจสอบว่ามี email อยู่แล้วหรือไม่
                        if not self.get_user_by_email(row['email']):
                            self.create_user(
                                email=row['email'],
                                name=row['name'],
                                is_admin=row.get('is_admin', 'false').lower() == 'true'
                            )
                            count += 1
                    except (ValueError, KeyError):
                        continue

            return count
        except Exception as e:
            print(f"Error importing users: {e}")
            return 0


# Singleton instance
_user_manager = None


def get_user_manager() -> UserManager:
    """
    Get singleton UserManager instance

    Returns:
        UserManager: instance
    """
    global _user_manager
    if _user_manager is None:
        _user_manager = UserManager()
    return _user_manager


if __name__ == "__main__":
    # Test
    um = get_user_manager()

    print(f"Total users: {len(um.get_all_users())}")
    print(f"Active users: {len(um.get_active_users())}")

    # Test get user
    user = um.get_user_by_email("pornthep.n@ntplc.co.th")
    if user:
        print(f"Found user: {user['name']} (Admin: {user['is_admin']})")
