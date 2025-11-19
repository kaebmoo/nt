# anomaly_web/app.py
"""
Anomaly Detection Web Application
Flask-based web interface for financial data anomaly detection
"""

from flask import Flask, render_template, request, redirect, url_for, jsonify, send_file, session, flash
from werkzeug.utils import secure_filename
import os
import json
import pandas as pd
from datetime import datetime
import uuid
from threading import Thread

from utils.file_handler import FileHandler
from utils.data_analyzer import DataAnalyzer
from utils.config_manager import ConfigManager
from utils.audit_runner import AuditRunner

app = Flask(__name__)
app.config.from_object('config.Config')

# Initialize utilities
file_handler = FileHandler(app.config['UPLOAD_FOLDER'], app.config['OUTPUT_FOLDER'])
data_analyzer = DataAnalyzer()
config_manager = ConfigManager(app.config['CONFIG_FOLDER'])
audit_runner = AuditRunner(app.config['PROGRESS_FOLDER'])

# ============================================================================
# HOME PAGE
# ============================================================================

@app.route('/')
def index():
    """หน้าแรก - แสดงตัวเลือกหลัก"""
    return render_template('index.html')

# ============================================================================
# FILE UPLOAD & PREVIEW
# ============================================================================

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    """อัพโหลดไฟล์และแสดง preview"""
    if request.method == 'GET':
        return render_template('upload.html')
    
    # Handle file upload
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    # Get metadata
    input_mode = request.form.get('input_mode', 'long')
    description = request.form.get('description', '')

    try:
        # Save file with metadata
        file_info = file_handler.save_upload(
            file=file,
            input_mode=input_mode,
            description=description
        )

        # Store in session
        session['current_file'] = file_info

        # Return JSON response with redirect URL for AJAX
        return jsonify({
            'success': True,
            'redirect': url_for('preview', file_id=file_info['file_id']),
            'file_id': file_info['file_id']
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/preview/<file_id>')
def preview(file_id):
    """แสดง preview ข้อมูลและ auto-detect columns"""
    try:
        # Load file info
        file_info = file_handler.get_file_info(file_id)
        if not file_info:
            flash('File not found', 'error')
            return redirect(url_for('upload'))
        
        # Read data for preview
        df = pd.read_csv(file_info['filepath'], nrows=100)
        
        # Auto-analyze data
        analysis = data_analyzer.analyze_dataframe(
            df=df,
            input_mode=file_info['input_mode']
        )
        
        # Prepare preview data
        preview_data = {
            'file_info': file_info,
            'shape': df.shape,
            'columns': df.columns.tolist(),
            'sample_data': df.head(20).to_dict('records'),
            'analysis': analysis
        }
        
        return render_template('preview.html', data=preview_data)
        
    except Exception as e:
        app.logger.error(f"Error loading preview for file_id {file_id}:", exc_info=True)
        flash(f'เกิดข้อผิดพลาดในการแสดงตัวอย่างข้อมูล: {str(e)}. กรุณาตรวจสอบว่าไฟล์เป็น CSV ที่ถูกต้องและลองอีกครั้ง', 'error')
        return redirect(url_for('upload'))

# ============================================================================
# CONFIGURATION
# ============================================================================

@app.route('/configure/<file_id>', methods=['GET', 'POST'])
def configure(file_id):
    """กำหนดค่า configuration สำหรับ anomaly detection"""
    
    if request.method == 'GET':
        # Load file info and analysis
        file_info = file_handler.get_file_info(file_id)
        if not file_info:
            flash('File not found', 'error')
            return redirect(url_for('upload'))
        
        # Load saved config if exists
        saved_config = config_manager.load_config(file_id)
        
        # Get column analysis
        df = pd.read_csv(file_info['filepath'], nrows=100)
        analysis = data_analyzer.analyze_dataframe(df, file_info['input_mode'])
        
        # Load config templates
        templates = config_manager.list_templates()
        
        return render_template(
            'configure.html',
            file_info=file_info,
            analysis=analysis,
            saved_config=saved_config,
            templates=templates
        )
    
    # POST - Save configuration
    config_data = request.get_json()
    
    try:
        # Validate configuration
        validation = config_manager.validate_config(config_data)
        if not validation['valid']:
            return jsonify({'error': validation['errors']}), 400
        
        # Save configuration
        config_manager.save_config(file_id, config_data)
        
        return jsonify({'success': True, 'message': 'Configuration saved'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/save-template', methods=['POST'])
def save_template():
    """บันทึก configuration template"""
    data = request.get_json()
    template_name = data.get('template_name')
    config_data = data.get('config')
    
    try:
        config_manager.save_template(template_name, config_data)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/load-template/<template_name>')
def load_template(template_name):
    """โหลด configuration template"""
    try:
        template = config_manager.load_template(template_name)
        return jsonify(template)
    except Exception as e:
        return jsonify({'error': str(e)}), 404

# ============================================================================
# PROCESSING
# ============================================================================

@app.route('/process/<file_id>')
def process(file_id):
    """หน้าแสดงการประมวลผล"""
    file_info = file_handler.get_file_info(file_id)
    config = config_manager.load_config(file_id)
    
    if not file_info or not config:
        flash('File or configuration not found', 'error')
        return redirect(url_for('upload'))
    
    return render_template('process.html', file_info=file_info, config=config)

def _run_audit_in_background(app_context, file_id, file_info, config, output_path):
    with app_context:
        try:
            # Run audit
            result = audit_runner.run_audit(
                input_file=file_info['filepath'],
                output_file=output_path,
                config=config,
                callback=lambda progress: update_progress(app_context, file_id, progress)
            )

            # Save output info
            output_info = file_handler.save_output_info(
                file_id=file_id,
                output_filename=os.path.basename(output_path),
                output_path=output_path,
                config=config,
                result=result
            )

            # Update final progress with output_id
            # Frontend will build the download URL from output_id
            update_progress(app_context, file_id, {
                'status': 'completed',
                'progress': 100,
                'message': 'Completed successfully',
                'result': result,
                'output_id': output_info['output_id']
            })

        except Exception as e:
            # Log the error or handle it appropriately
            print(f"Error in background audit for file_id {file_id}: {e}")
            import traceback
            traceback.print_exc()
            # Optionally, update progress with an error status
            update_progress(app_context, file_id, {'status': 'error', 'message': str(e)})

@app.route('/api/run-audit/<file_id>', methods=['POST'])
def run_audit(file_id):
    """รัน anomaly detection (Async with progress tracking)"""
    try:
        # Get file info and config
        file_info = file_handler.get_file_info(file_id)
        config = config_manager.load_config(file_id)
        
        if not file_info or not config:
            return jsonify({'error': 'File or configuration not found'}), 404
        
        # Generate output filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        base_name = os.path.splitext(file_info['original_filename'])[0]
        output_filename = f"{base_name}_audit_{timestamp}.xlsx"
        output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
        
        # Start audit in a new thread
        app_context = app.app_context()
        thread = Thread(target=_run_audit_in_background, args=(app_context, file_id, file_info, config, output_path))
        thread.start()
        
        return jsonify({
            'success': True,
            'message': 'Audit started in background',
            'output_filename': output_filename # Provide filename for client-side tracking if needed
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/progress/<file_id>')
def get_progress(file_id):
    """ดึง progress ของการประมวลผล"""
    progress = audit_runner.get_progress(file_id)
    return jsonify(progress)

def update_progress(app_context, file_id, progress):
    """Update progress (callback function)"""
    with app_context:
        audit_runner.update_progress(file_id, progress)

# ============================================================================
# DOWNLOAD & HISTORY
# ============================================================================

@app.route('/download/<output_id>')
def download_output(output_id):
    """ดาวน์โหลดไฟล์ผลลัพธ์"""
    try:
        output_info = file_handler.get_output_info(output_id)
        if not output_info:
            flash('Output file not found', 'error')
            return redirect(url_for('history'))
        
        return send_file(
            output_info['filepath'],
            as_attachment=True,
            download_name=output_info['filename']
        )
    except Exception as e:
        flash(f'Error downloading file: {str(e)}', 'error')
        return redirect(url_for('history'))

@app.route('/history')
def history():
    """แสดงประวัติการทำงานทั้งหมด"""
    # Get all files and outputs
    uploads = file_handler.list_uploads()
    outputs = file_handler.list_outputs()
    
    return render_template('history.html', uploads=uploads, outputs=outputs)

@app.route('/api/upload-metadata/<file_id>', methods=['POST'])
def update_upload_metadata(file_id):
    """อัพเดท description และ tags ของไฟล์ input"""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid JSON'}), 400
        
    description = data.get('description')
    tags = data.get('tags') # Expect a list of strings

    try:
        success = file_handler.update_upload_metadata(file_id, description=description, tags=tags)
        if success:
            return jsonify({'success': True, 'message': 'Metadata updated successfully.'})
        else:
            return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        app.logger.error(f"Error updating metadata for file_id {file_id}:", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/delete-file/<file_id>', methods=['DELETE'])
def delete_file(file_id):
    """ลบไฟล์ input"""
    try:
        file_handler.delete_upload(file_id)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/delete-output/<output_id>', methods=['DELETE'])
def delete_output(output_id):
    """ลบไฟล์ output"""
    try:
        file_handler.delete_output(output_id)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500

# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    # Create necessary directories
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)
    os.makedirs(app.config['CONFIG_FOLDER'], exist_ok=True)
    
    app.run(debug=True, host='0.0.0.0', port=9000)
