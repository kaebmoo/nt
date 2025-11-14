"""
Job Scheduler
Handles scheduled and manual ETL job execution
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
import pytz


class JobScheduler:
    """Manages scheduled ETL jobs"""

    def __init__(self, config_manager, etl_runner, logger):
        """
        Initialize job scheduler

        Args:
            config_manager: ConfigManager instance
            etl_runner: ETLRunner instance
            logger: JSONLogger instance
        """
        self.config = config_manager
        self.etl_runner = etl_runner
        self.logger = logger
        self.scheduler = BackgroundScheduler()

    def start(self):
        """Start the scheduler"""
        if not self.scheduler.running:
            self._setup_jobs()
            self.scheduler.start()
            self.logger.info("Job scheduler started")

    def shutdown(self):
        """Shutdown the scheduler"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            self.logger.info("Job scheduler shutdown")

    def _setup_jobs(self):
        """Setup scheduled jobs from configuration"""
        etl_config = self.config.get_etl_config()
        schedule = etl_config.get('schedule', {})

        if not schedule.get('enabled', False):
            self.logger.info("Scheduled jobs are disabled")
            return

        # Get schedule parameters
        day_of_month = schedule.get('day_of_month', 10)
        hour = schedule.get('hour', 2)
        minute = schedule.get('minute', 0)
        timezone_str = schedule.get('timezone', 'Asia/Bangkok')

        try:
            timezone = pytz.timezone(timezone_str)
        except pytz.exceptions.UnknownTimeZoneError:
            self.logger.warning(f"Unknown timezone: {timezone_str}, using UTC")
            timezone = pytz.UTC

        # Create cron trigger (monthly on specified day)
        trigger = CronTrigger(
            day=day_of_month,
            hour=hour,
            minute=minute,
            timezone=timezone
        )

        # Add job to scheduler
        self.scheduler.add_job(
            self._run_monthly_etl,
            trigger=trigger,
            id='monthly_etl',
            name='Monthly Revenue ETL',
            replace_existing=True
        )

        self.logger.info(
            f"Scheduled monthly ETL job: day {day_of_month} at {hour:02d}:{minute:02d} {timezone_str}"
        )

    def _run_monthly_etl(self):
        """Run the monthly ETL job sequence"""
        self.logger.info("Starting scheduled monthly ETL job")

        etl_config = self.config.get_etl_config()
        scripts = etl_config.get('scripts', {})

        # Run scripts in sequence
        # 1. fi_revenue_expense.py
        script1 = scripts.get('fi_revenue_expense', 'fi_revenue_expense')
        result1 = self.etl_runner.run_script(script1, triggered_by="scheduler")

        if result1['status'] != 'completed':
            self.logger.error(f"First script failed, stopping sequence: {result1.get('error')}")
            return

        # 2. revenue_etl_report.py
        script2 = scripts.get('revenue_etl_report', 'revenue_etl_report')
        result2 = self.etl_runner.run_script(script2, triggered_by="scheduler")

        if result2['status'] != 'completed':
            self.logger.error(f"Second script failed: {result2.get('error')}")
            return

        # Optional: 3. revenue_reconciliation.py
        if 'revenue_reconciliation' in scripts:
            script3 = scripts.get('revenue_reconciliation')
            result3 = self.etl_runner.run_script(script3, triggered_by="scheduler")

        self.logger.info("Monthly ETL job sequence completed")

    def run_manual_job(self, script_name: str, triggered_by: str) -> dict:
        """
        Run ETL job manually (triggered by user)

        Args:
            script_name: Name of script to run
            triggered_by: Email of user who triggered the job

        Returns:
            Job result dict
        """
        self.logger.info(f"Manual job triggered by {triggered_by}: {script_name}")
        return self.etl_runner.run_script(script_name, triggered_by=triggered_by)

    def get_next_run_time(self) -> str:
        """Get next scheduled run time"""
        job = self.scheduler.get_job('monthly_etl')
        if job and job.next_run_time:
            return job.next_run_time.strftime('%Y-%m-%d %H:%M:%S %Z')
        return "Not scheduled"

    def get_scheduler_status(self) -> dict:
        """Get scheduler status information"""
        etl_config = self.config.get_etl_config()
        schedule = etl_config.get('schedule', {})

        return {
            "running": self.scheduler.running,
            "enabled": schedule.get('enabled', False),
            "next_run": self.get_next_run_time(),
            "jobs": [
                {
                    "id": job.id,
                    "name": job.name,
                    "next_run": job.next_run_time.strftime('%Y-%m-%d %H:%M:%S %Z') if job.next_run_time else None
                }
                for job in self.scheduler.get_jobs()
            ]
        }
