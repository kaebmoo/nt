"""
Queue Manager for RQ
Handles Redis Queue connections and job management
"""

import os
from redis import Redis
from redis.exceptions import ConnectionError as RedisConnectionError
from rq import Queue


class QueueManager:
    """Manages RQ queues for async tasks"""

    def __init__(self):
        """Initialize queue manager"""
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

        try:
            self.redis_conn = Redis.from_url(redis_url, socket_connect_timeout=2)
            # Test connection
            self.redis_conn.ping()
            self.is_available = True
            self.email_queue = Queue('email', connection=self.redis_conn)
            self.default_queue = Queue('default', connection=self.redis_conn)
        except (RedisConnectionError, Exception) as e:
            print(f"⚠️  Redis connection failed: {e}")
            print(f"⚠️  RQ features disabled, will use synchronous email sending")
            self.is_available = False
            self.redis_conn = None
            self.email_queue = None
            self.default_queue = None

    def enqueue_email(self, task_func, *args, **kwargs):
        """
        Enqueue email task

        Args:
            task_func: Task function to execute
            *args: Positional arguments for task
            **kwargs: Keyword arguments for task

        Returns:
            Job object if successful, None if Redis not available
        """
        if not self.is_available:
            return None

        try:
            job = self.email_queue.enqueue(
                task_func,
                *args,
                job_timeout='5m',
                **kwargs
            )
            return job
        except Exception as e:
            print(f"⚠️  Failed to enqueue email task: {e}")
            return None

    def get_job(self, job_id: str):
        """
        Get job by ID

        Args:
            job_id: Job ID

        Returns:
            Job object or None
        """
        if not self.is_available or not job_id:
            return None

        try:
            from rq.job import Job
            return Job.fetch(job_id, connection=self.redis_conn)
        except Exception:
            return None

    def get_job_status(self, job_id: str) -> dict:
        """
        Get job status

        Args:
            job_id: Job ID

        Returns:
            Dict with job status information
        """
        if not self.is_available:
            return {'status': 'unavailable', 'message': 'Redis not available'}

        job = self.get_job(job_id)

        if not job:
            return {'status': 'not_found', 'message': 'Job not found'}

        result = {
            'status': job.get_status(),
            'created_at': job.created_at.isoformat() if job.created_at else None,
            'ended_at': job.ended_at.isoformat() if job.ended_at else None,
        }

        if job.is_finished:
            result['result'] = job.result

        if job.is_failed:
            result['error'] = str(job.exc_info) if job.exc_info else 'Unknown error'

        return result
