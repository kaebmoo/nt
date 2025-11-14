#!/usr/bin/env python3
"""
RQ Worker for Revenue ETL Web Application
Processes async email tasks from Redis Queue

Usage:
    python rq_worker.py

    Or with specific Redis connection:
    REDIS_URL=redis://localhost:6379/0 python rq_worker.py
"""

import os
import sys
from redis import Redis
from rq import Worker, Queue, Connection

# Add app directory to path
sys.path.insert(0, os.path.dirname(__file__))

# Flask app context (needed for config access)
from app import create_app

app = create_app()

# Redis connection
redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
redis_conn = Redis.from_url(redis_url)

if __name__ == '__main__':
    with app.app_context():
        # Listen to email queue
        with Connection(redis_conn):
            worker = Worker(['email', 'default'], connection=redis_conn)
            print(f"✓ RQ Worker started, listening to: email, default")
            print(f"✓ Redis: {redis_url}")
            print(f"✓ Press Ctrl+C to stop\n")
            worker.work()
