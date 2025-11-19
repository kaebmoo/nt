"""
ETL Integration Module
======================
จัดการการ import และ integration ระหว่าง Web App และ ETL System
แก้ปัญหา naming collision และ path management

Author: Revenue Report Web Integration
Version: 1.0.0
"""

import sys
import os
from pathlib import Path
from typing import Optional
import importlib.util

# ========== Path Configuration ==========
# ETL System base path
# Default: sibling directory (revenue-report) next to this app (revenue-report-web)
# Can be overridden by environment variable ETL_BASE_PATH
_default_etl_path = os.path.abspath(os.path.join(
    os.path.dirname(__file__),  # revenue-report-web/
    '..',                       # nt/
    'revenue-report'            # revenue-report/
))
ETL_BASE_PATH = os.environ.get('ETL_BASE_PATH', _default_etl_path)
ETL_CONFIG_FILE = 'config.json'

# Track if ETL imports have been set up
_etl_imports_setup = False
_etl_modules_cache = {}

def setup_etl_imports():
    """
    ตั้งค่า sys.path เพื่อให้ import ETL modules ได้
    เรียกครั้งเดียวเมื่อต้องการใช้งาน ETL modules จริง

    Returns:
        bool: True ถ้าตั้งค่าสำเร็จ
    """
    global _etl_imports_setup

    if _etl_imports_setup:
        return True

    if not os.path.exists(ETL_BASE_PATH):
        raise FileNotFoundError(f"ETL base path not found: {ETL_BASE_PATH}")

    # Add ETL path to sys.path if not already there (ท้ายสุดเพื่อไม่ให้แทนที่ web app modules)
    if ETL_BASE_PATH not in sys.path:
        # Append to end (NOT insert at 0) to prevent overriding web app's imports
        sys.path.append(ETL_BASE_PATH)

    _etl_imports_setup = True
    return True


# ========== Import ETL Modules ==========
# NOTE: Import happens lazily when setup_etl_imports() is called

def _import_module_from_path(module_name: str, file_path: str):
    """
    Import a module from a specific file path

    Args:
        module_name: Name for the module (e.g., 'etl_config_manager')
        file_path: Full path to the .py file

    Returns:
        The imported module
    """
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load module from {file_path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _lazy_import_etl_modules():
    """
    Import ETL modules lazily using importlib to avoid path pollution
    Only called when actually needed
    """
    global _etl_modules_cache

    if _etl_modules_cache:
        return _etl_modules_cache

    try:
        # Setup sys.path first so ETL modules can import their dependencies
        setup_etl_imports()

        # CRITICAL: Save ALL web app's modules before importing ETL modules
        _web_app_modules = ['config_manager', 'user_manager', 'auth_manager', 'email_sender']
        saved_modules = {}
        for module_name in _web_app_modules:
            if module_name in sys.modules:
                saved_modules[module_name] = sys.modules[module_name]

        # Import ConfigManager from ETL system using absolute path
        etl_config_manager_path = os.path.join(ETL_BASE_PATH, 'config_manager.py')
        etl_config_module = _import_module_from_path('_etl_config_manager', etl_config_manager_path)
        ETLConfigManager = etl_config_module.ConfigManager

        # Temporarily inject ETL's config_manager so main.py can use it
        sys.modules['config_manager'] = etl_config_module

        # Import main.py (now it will use ETL's get_config_manager)
        etl_main_path = os.path.join(ETL_BASE_PATH, 'main.py')
        etl_main_module = _import_module_from_path('_etl_main', etl_main_path)
        RevenueETLSystem = etl_main_module.RevenueETLSystem

        # RESTORE ALL web app's modules immediately after import
        for module_name, module in saved_modules.items():
            sys.modules[module_name] = module

        # If no original modules, ensure ETL's versions are removed
        if not saved_modules.get('config_manager'):
            sys.modules.pop('config_manager', None)

        # Import FI module
        etl_fi_path = os.path.join(ETL_BASE_PATH, 'fi_revenue_expense_module.py')
        etl_fi_module = _import_module_from_path('_etl_fi_module', etl_fi_path)
        FIRevenueExpenseProcessor = etl_fi_module.FIRevenueExpenseProcessor

        # Import logger
        etl_logger_path = os.path.join(ETL_BASE_PATH, 'logger_utils.py')
        etl_logger_module = _import_module_from_path('_etl_logger_utils', etl_logger_path)
        ETLLogger = etl_logger_module.ETLLogger

        _etl_modules_cache = {
            'ETLConfigManager': ETLConfigManager,
            'RevenueETLSystem': RevenueETLSystem,
            'FIRevenueExpenseProcessor': FIRevenueExpenseProcessor,
            'ETLLogger': ETLLogger,
            'etl_config_module': etl_config_module,
            'available': True,
            'error': None
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        _etl_modules_cache = {
            'available': False,
            'error': str(e)
        }

    return _etl_modules_cache


# Expose classes via properties
def _get_etl_class(class_name):
    """Helper to get ETL class lazily"""
    modules = _lazy_import_etl_modules()
    if not modules.get('available'):
        # Return dummy class
        class DummyClass:
            pass
        return DummyClass
    return modules.get(class_name)

# Create lazy accessors
class _LazyETLConfigManager:
    def __new__(cls, *args, **kwargs):
        real_class = _get_etl_class('ETLConfigManager')
        return real_class(*args, **kwargs)

class _LazyRevenueETLSystem:
    def __new__(cls, *args, **kwargs):
        real_class = _get_etl_class('RevenueETLSystem')
        return real_class(*args, **kwargs)

class _LazyFIRevenueExpenseProcessor:
    def __new__(cls, *args, **kwargs):
        real_class = _get_etl_class('FIRevenueExpenseProcessor')
        return real_class(*args, **kwargs)

class _LazyETLLogger:
    @staticmethod
    def get_logger(name):
        logger_class = _get_etl_class('ETLLogger')
        if hasattr(logger_class, 'get_logger'):
            return logger_class.get_logger(name)
        import logging
        return logging.getLogger(name)

# Export lazy wrappers
ETLConfigManager = _LazyETLConfigManager
RevenueETLSystem = _LazyRevenueETLSystem
FIRevenueExpenseProcessor = _LazyFIRevenueExpenseProcessor
ETLLogger = _LazyETLLogger

# Compatibility
ETL_MODULES_AVAILABLE = None  # Will be determined lazily
ETL_IMPORT_ERROR = None


# ========== Helper Functions ==========

def check_etl_modules_available() -> tuple[bool, Optional[str]]:
    """
    ตรวจสอบว่า ETL modules สามารถ import ได้หรือไม่

    Returns:
        tuple: (available: bool, error_message: Optional[str])
    """
    modules = _lazy_import_etl_modules()
    available = modules.get('available', False)
    error = modules.get('error')
    return available, error


def get_etl_config_path() -> str:
    """
    ดึง path ของไฟล์ config.json ของ ETL system

    Returns:
        str: Full path ของ config.json
    """
    return os.path.join(ETL_BASE_PATH, ETL_CONFIG_FILE)


def create_etl_config_manager():
    """
    สร้าง ETL ConfigManager instance

    Returns:
        ETLConfigManager instance หรือ None ถ้าไม่สามารถสร้างได้
    """
    # Check if modules available
    available, error = check_etl_modules_available()
    if not available:
        print(f"ETL modules not available: {error}")
        return None

    try:
        config_path = get_etl_config_path()

        if not os.path.exists(config_path):
            raise FileNotFoundError(f"ETL config file not found: {config_path}")

        # Get real class from cache
        modules = _lazy_import_etl_modules()
        RealETLConfigManager = modules.get('ETLConfigManager')

        # Debug: Check which module we're using
        print(f"[DEBUG] ETLConfigManager class: {RealETLConfigManager}")
        print(f"[DEBUG] Config path: {config_path}")

        # Create config manager instance
        config_manager = RealETLConfigManager(config_path)

        return config_manager

    except Exception as e:
        import traceback
        print(f"Error creating ETL config manager: {e}")
        print(f"[DEBUG] Full traceback:")
        traceback.print_exc()
        return None


def create_etl_system():
    """
    สร้าง RevenueETLSystem instance

    Returns:
        RevenueETLSystem instance หรือ None ถ้าไม่สามารถสร้างได้
    """
    # Check if modules available
    available, error = check_etl_modules_available()
    if not available:
        print(f"ETL modules not available: {error}")
        return None

    try:
        config_path = get_etl_config_path()

        if not os.path.exists(config_path):
            raise FileNotFoundError(f"ETL config file not found: {config_path}")

        # Get real class from cache
        modules = _lazy_import_etl_modules()
        RealRevenueETLSystem = modules.get('RevenueETLSystem')

        # Debug: Check RevenueETLSystem
        print(f"[DEBUG] RevenueETLSystem class: {RealRevenueETLSystem}")
        print(f"[DEBUG] Creating with config_path: {config_path}")

        # Create system instance
        system = RealRevenueETLSystem(config_path)

        return system

    except Exception as e:
        import traceback
        print(f"Error creating ETL system: {e}")
        print(f"[DEBUG] Full traceback:")
        traceback.print_exc()
        return None


def validate_etl_environment() -> dict:
    """
    ตรวจสอบ environment สำหรับ ETL integration

    Returns:
        dict: {
            'valid': bool,
            'etl_base_exists': bool,
            'config_file_exists': bool,
            'modules_available': bool,
            'errors': list
        }
    """
    errors = []

    # Check base path
    etl_base_exists = os.path.exists(ETL_BASE_PATH)
    if not etl_base_exists:
        errors.append(f"ETL base path not found: {ETL_BASE_PATH}")

    # Check config file
    config_path = get_etl_config_path()
    config_file_exists = os.path.exists(config_path)
    if not config_file_exists:
        errors.append(f"ETL config file not found: {config_path}")

    # Check modules
    modules_available, import_error = check_etl_modules_available()
    if not modules_available:
        errors.append(f"ETL modules import failed: {import_error}")

    valid = etl_base_exists and config_file_exists and modules_available

    return {
        'valid': valid,
        'etl_base_exists': etl_base_exists,
        'config_file_exists': config_file_exists,
        'modules_available': modules_available,
        'errors': errors
    }


# ========== Export ==========
__all__ = [
    'ETL_BASE_PATH',
    'ETL_CONFIG_FILE',
    'ETLConfigManager',
    'RevenueETLSystem',
    'FIRevenueExpenseProcessor',
    'ETLLogger',
    'setup_etl_imports',
    'check_etl_modules_available',
    'get_etl_config_path',
    'create_etl_config_manager',
    'create_etl_system',
    'validate_etl_environment',
]


if __name__ == "__main__":
    # Test integration
    print("=" * 80)
    print("ETL Integration Module - Test")
    print("=" * 80)

    # Validate environment
    validation = validate_etl_environment()

    print(f"\nValidation Results:")
    print(f"  Valid: {validation['valid']}")
    print(f"  ETL Base Exists: {validation['etl_base_exists']}")
    print(f"  Config File Exists: {validation['config_file_exists']}")
    print(f"  Modules Available: {validation['modules_available']}")

    if validation['errors']:
        print(f"\nErrors:")
        for error in validation['errors']:
            print(f"  - {error}")

    # Try creating config manager
    if validation['valid']:
        print("\nTrying to create ETL Config Manager...")
        config_manager = create_etl_config_manager()

        if config_manager:
            print("  ✓ Success!")
            print(f"  Year: {config_manager.get_year()}")
            print(f"  OS Platform: {config_manager.os_platform}")
        else:
            print("  ✗ Failed to create config manager")

    print("\n" + "=" * 80)
