# anomaly_web/utils/config_manager.py
"""
Configuration Manager
จัดการ configuration ของ anomaly detection
รองรับ save/load configuration และ templates
"""

import os
import json
from datetime import datetime

class ConfigManager:
    """จัดการ configuration และ templates"""
    
    def __init__(self, config_folder):
        self.config_folder = config_folder
        self.templates_folder = os.path.join(config_folder, 'templates')
        
        # Create folders
        os.makedirs(config_folder, exist_ok=True)
        os.makedirs(self.templates_folder, exist_ok=True)
    
    def save_config(self, file_id, config_data):
        """บันทึก configuration สำหรับ file_id นั้นๆ"""
        config_path = os.path.join(self.config_folder, f"{file_id}.json")
        
        # Add metadata
        config_data['_metadata'] = {
            'file_id': file_id,
            'saved_at': datetime.now().isoformat(),
            'version': '1.0'
        }
        
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, ensure_ascii=False, indent=2)
        
        return config_path
    
    def load_config(self, file_id):
        """โหลด configuration"""
        config_path = os.path.join(self.config_folder, f"{file_id}.json")
        
        if not os.path.exists(config_path):
            return None
        
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def validate_config(self, config_data):
        """
        ตรวจสอบความถูกต้องของ configuration
        
        Returns:
            dict: {'valid': bool, 'errors': []}
        """
        errors = []
        
        # Required fields
        required_fields = [
            'input_mode',
            'target_col',
            'crosstab_dimensions'
        ]
        
        for field in required_fields:
            if field not in config_data or not config_data[field]:
                errors.append(f"Missing required field: {field}")
        
        # Input mode validation
        if config_data.get('input_mode') not in ['long', 'crosstab']:
            errors.append("input_mode must be 'long' or 'crosstab'")
        
        # Crosstab mode validation
        if config_data.get('input_mode') == 'crosstab':
            crosstab_required = ['crosstab_id_vars', 'crosstab_value_name']
            for field in crosstab_required:
                if field not in config_data or not config_data[field]:
                    errors.append(f"Crosstab mode requires: {field}")
        
        # Long mode validation
        if config_data.get('input_mode') == 'long':
            # ต้องมี YEAR+MONTH หรือ DATE
            has_year_month = config_data.get('col_year') and config_data.get('col_month')
            has_date = config_data.get('date_column')
            
            if not (has_year_month or has_date):
                errors.append("Long mode requires either (YEAR + MONTH) or DATE column")
        
        # Dimension validation
        dimensions = config_data.get('crosstab_dimensions', [])
        if not isinstance(dimensions, list) or len(dimensions) == 0:
            errors.append("crosstab_dimensions must be a non-empty list")
        
        # Analysis options validation
        if not config_data.get('run_time_series_analysis') and not config_data.get('run_peer_group_analysis'):
            errors.append("At least one analysis method must be enabled")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
    
    def save_template(self, template_name, config_data):
        """บันทึก configuration template"""
        template_path = os.path.join(self.templates_folder, f"{template_name}.json")
        
        # Remove file-specific metadata
        template_data = {k: v for k, v in config_data.items() if not k.startswith('_')}
        
        # Add template metadata
        template_data['_template'] = {
            'name': template_name,
            'created_at': datetime.now().isoformat(),
            'version': '1.0'
        }
        
        with open(template_path, 'w', encoding='utf-8') as f:
            json.dump(template_data, f, ensure_ascii=False, indent=2)
        
        return template_path
    
    def load_template(self, template_name):
        """โหลด configuration template"""
        template_path = os.path.join(self.templates_folder, f"{template_name}.json")
        
        if not os.path.exists(template_path):
            raise FileNotFoundError(f"Template '{template_name}' not found")
        
        with open(template_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def list_templates(self):
        """แสดงรายการ templates ทั้งหมด"""
        templates = []
        
        if not os.path.exists(self.templates_folder):
            return templates
        
        for filename in os.listdir(self.templates_folder):
            if filename.endswith('.json'):
                template_name = filename[:-5]  # Remove .json
                template_path = os.path.join(self.templates_folder, filename)
                
                try:
                    with open(template_path, 'r', encoding='utf-8') as f:
                        template_data = json.load(f)
                    
                    templates.append({
                        'name': template_name,
                        'metadata': template_data.get('_template', {}),
                        'description': self._generate_template_description(template_data)
                    })
                except:
                    pass
        
        return templates
    
    def _generate_template_description(self, config_data):
        """สร้างคำอธิบาย template"""
        parts = []
        
        # Input mode
        parts.append(f"Mode: {config_data.get('input_mode', 'unknown')}")
        
        # Analysis methods
        methods = []
        if config_data.get('run_time_series_analysis'):
            methods.append('Time Series')
        if config_data.get('run_peer_group_analysis'):
            methods.append('Peer Group')
        
        if methods:
            parts.append(f"Analysis: {', '.join(methods)}")
        
        # Dimensions
        dims = config_data.get('crosstab_dimensions', [])
        if dims:
            parts.append(f"Dimensions: {len(dims)}")
        
        return ' | '.join(parts)
    
    def delete_template(self, template_name):
        """ลบ template"""
        template_path = os.path.join(self.templates_folder, f"{template_name}.json")
        
        if os.path.exists(template_path):
            os.remove(template_path)
            return True
        return False
