"""
ETL Runner
Executes ETL scripts and captures output
"""

import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import uuid


class ETLRunner:
    """Runs ETL scripts and manages execution"""

    def __init__(self, config_manager, logger, email_sender):
        """
        Initialize ETL runner

        Args:
            config_manager: ConfigManager instance
            logger: JSONLogger instance
            email_sender: EmailSender instance
        """
        self.config = config_manager
        self.logger = logger
        self.email_sender = email_sender

    def run_script(
        self,
        script_name: str,
        params: Optional[Dict[str, Any]] = None,
        triggered_by: str = "system"
    ) -> Dict[str, Any]:
        """
        Run ETL script

        Args:
            script_name: Name of the script to run
            params: Optional parameters for the script
            triggered_by: Who triggered the job (email or "system")

        Returns:
            Dict with job result information
        """
        # Generate job ID
        job_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"

        # Get script path
        etl_config = self.config.get_etl_config()
        script_path = self._get_script_path(script_name)

        if not script_path or not script_path.exists():
            error = f"Script not found: {script_name}"
            self.logger.error(error)
            return {
                "job_id": job_id,
                "status": "failed",
                "error": error
            }

        # Log job start
        self.logger.log_job_start(job_id, script_name, params)
        self.logger.info(f"Starting ETL job {job_id}: {script_name} (triggered by {triggered_by})")

        try:
            # Run script
            result = self._execute_script(script_path, job_id)

            # Log completion
            success = result['returncode'] == 0
            error = result.get('error')

            self.logger.log_job_complete(job_id, success, error)

            # Send notification if enabled
            self._send_notification(job_id, script_name, success, error, triggered_by)

            return {
                "job_id": job_id,
                "status": "completed" if success else "failed",
                "script": script_name,
                "output": result.get('output', ''),
                "error": error,
                "returncode": result['returncode']
            }

        except Exception as e:
            error = f"Exception running script: {str(e)}"
            self.logger.log_job_complete(job_id, False, error)
            self.logger.error(error)

            return {
                "job_id": job_id,
                "status": "failed",
                "error": error
            }

    def _get_script_path(self, script_name: str) -> Optional[Path]:
        """Get full path to ETL script"""
        etl_config = self.config.get_etl_config()
        etl_dir = Path(etl_config.get('paths', {}).get('etl_scripts', 'etl'))

        # Try different extensions
        for ext in ['.py', '']:
            script_path = etl_dir / f"{script_name}{ext}"
            if script_path.exists():
                return script_path

        return None

    def _execute_script(self, script_path: Path, job_id: str) -> Dict[str, Any]:
        """
        Execute Python script and capture output

        Args:
            script_path: Path to script
            job_id: Job ID for logging

        Returns:
            Dict with execution result
        """
        try:
            # Run script with Python interpreter
            process = subprocess.Popen(
                [sys.executable, str(script_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )

            # Capture output line by line
            output_lines = []
            for line in process.stdout:
                line = line.rstrip()
                output_lines.append(line)
                self.logger.log_job_output(job_id, line)

            # Wait for completion
            process.wait()

            return {
                "returncode": process.returncode,
                "output": "\n".join(output_lines),
                "error": None if process.returncode == 0 else "Script exited with non-zero code"
            }

        except Exception as e:
            return {
                "returncode": 1,
                "output": "",
                "error": str(e)
            }

    def _send_notification(
        self,
        job_id: str,
        script_name: str,
        success: bool,
        error: Optional[str],
        triggered_by: str
    ):
        """Send email notification about job completion"""
        etl_config = self.config.get_etl_config()
        notifications = etl_config.get('notifications', {})

        if not notifications.get('enabled', False):
            return

        # Check if should notify for this result
        if success and not notifications.get('on_success', True):
            return
        if not success and not notifications.get('on_failure', True):
            return

        # Get recipients
        recipients = notifications.get('recipients', [])
        if triggered_by != "system" and triggered_by not in recipients:
            recipients.append(triggered_by)

        if not recipients:
            return

        # Build notification message
        status = "✓ Completed Successfully" if success else "✗ Failed"
        subject = f"ETL Job {status}: {script_name}"

        message = f"""
Job ID: {job_id}
Script: {script_name}
Status: {status}
Triggered by: {triggered_by}
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

        if error:
            message += f"\nError:\n{error}"

        # Send to all recipients
        for recipient in recipients:
            try:
                self.email_sender.send_notification(recipient, subject, message)
            except Exception as e:
                self.logger.error(f"Failed to send notification to {recipient}: {e}")
