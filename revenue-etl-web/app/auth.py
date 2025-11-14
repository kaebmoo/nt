"""
Authentication System
OTP-based authentication without password
"""

import json
import secrets
import string
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any
from functools import wraps
from flask import session, redirect, url_for, request


class AuthManager:
    """Manages OTP-based authentication"""

    def __init__(self, config_manager, email_sender, logger, queue_manager=None):
        """
        Initialize authentication manager

        Args:
            config_manager: ConfigManager instance
            email_sender: EmailSender instance
            logger: JSONLogger instance
            queue_manager: QueueManager instance (optional)
        """
        self.config = config_manager
        self.email_sender = email_sender
        self.logger = logger
        self.queue_manager = queue_manager

        self.sessions_dir = Path("data/sessions")
        self.sessions_dir.mkdir(parents=True, exist_ok=True)

    def generate_otp(self, length: int = 6) -> str:
        """Generate random OTP code"""
        digits = string.digits
        return ''.join(secrets.choice(digits) for _ in range(length))

    def send_otp(self, email: str) -> bool:
        """
        Generate and send OTP to email

        Args:
            email: User email address

        Returns:
            True if OTP sent successfully, False otherwise
        """
        # Check if domain is allowed
        if not self.config.is_allowed_domain(email):
            self.logger.warning(f"OTP request from unauthorized domain: {email}")
            return False

        # Generate OTP
        auth_config = self.config.get_auth_config()
        otp_config = self.config.get_email_config().get('otp', {})

        otp_code = self.generate_otp(otp_config.get('length', 6))
        expiry_minutes = otp_config.get('expiry_minutes', 10)
        expiry_time = datetime.now() + timedelta(minutes=expiry_minutes)

        # Store OTP in session file
        otp_data = {
            "email": email,
            "otp": otp_code,
            "expiry": expiry_time.isoformat(),
            "attempts": 0,
            "max_attempts": 3
        }

        session_file = self.sessions_dir / f"otp_{email.replace('@', '_at_')}.json"
        self._save_json(session_file, otp_data)

        # Try to send OTP via RQ worker (async) with fallback to sync
        success = False
        job_id = None

        # Try RQ first (if available)
        if self.queue_manager and self.queue_manager.is_available:
            try:
                from app.utils.email_tasks import send_otp_email_task

                job = self.queue_manager.enqueue_email(
                    send_otp_email_task,
                    recipient_email=email,
                    otp_code=otp_code
                )

                if job:
                    job_id = job.id
                    # Store job_id in session for tracking
                    session['email_job_id'] = job_id
                    success = True
                    self.logger.info(f"OTP queued for {email}, job_id: {job_id}")

            except Exception as e:
                self.logger.warning(f"RQ failed, falling back to sync email: {e}")

        # Fallback to synchronous email sending
        if not success:
            success = self.email_sender.send_otp(email, otp_code)

        if success:
            self.logger.log_access(email, "otp_sent", {
                "expiry": expiry_time.isoformat(),
                "async": job_id is not None,
                "job_id": job_id
            })
        else:
            self.logger.warning(f"Failed to send OTP to {email}")

        return success

    def verify_otp(self, email: str, otp_code: str) -> bool:
        """
        Verify OTP code

        Args:
            email: User email address
            otp_code: OTP code to verify

        Returns:
            True if OTP is valid, False otherwise
        """
        session_file = self.sessions_dir / f"otp_{email.replace('@', '_at_')}.json"

        if not session_file.exists():
            self.logger.warning(f"OTP verification failed: No OTP found for {email}")
            return False

        otp_data = self._load_json(session_file)
        if not otp_data:
            return False

        # Check attempts
        if otp_data.get('attempts', 0) >= otp_data.get('max_attempts', 3):
            self.logger.warning(f"OTP verification failed: Max attempts exceeded for {email}")
            session_file.unlink()  # Delete session
            return False

        # Check expiry
        expiry = datetime.fromisoformat(otp_data.get('expiry'))
        if datetime.now() > expiry:
            self.logger.warning(f"OTP verification failed: Expired for {email}")
            session_file.unlink()  # Delete session
            return False

        # Verify OTP
        if otp_data.get('otp') == otp_code:
            # OTP valid - create session
            self.create_session(email)
            session_file.unlink()  # Delete OTP session
            self.logger.log_access(email, "login_success")
            return True
        else:
            # Increment attempts
            otp_data['attempts'] += 1
            self._save_json(session_file, otp_data)
            self.logger.warning(f"OTP verification failed: Invalid code for {email}")
            return False

    def create_session(self, email: str) -> str:
        """
        Create user session

        Args:
            email: User email address

        Returns:
            Session ID
        """
        session_id = secrets.token_urlsafe(32)

        auth_config = self.config.get_auth_config()
        timeout_minutes = auth_config.get('session', {}).get('timeout_minutes', 60)
        expiry_time = datetime.now() + timedelta(minutes=timeout_minutes)

        session_data = {
            "session_id": session_id,
            "email": email,
            "is_admin": self.config.is_admin(email),
            "created_at": datetime.now().isoformat(),
            "expiry": expiry_time.isoformat(),
            "last_activity": datetime.now().isoformat()
        }

        # Save session
        session_file = self.sessions_dir / f"session_{session_id}.json"
        self._save_json(session_file, session_data)

        # Set Flask session
        session['session_id'] = session_id
        session['email'] = email
        session['is_admin'] = session_data['is_admin']

        return session_id

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get session data

        Args:
            session_id: Session ID

        Returns:
            Session data dict or None if not found/expired
        """
        session_file = self.sessions_dir / f"session_{session_id}.json"

        if not session_file.exists():
            return None

        session_data = self._load_json(session_file)
        if not session_data:
            return None

        # Check expiry
        expiry = datetime.fromisoformat(session_data.get('expiry'))
        if datetime.now() > expiry:
            session_file.unlink()  # Delete expired session
            return None

        # Update last activity
        session_data['last_activity'] = datetime.now().isoformat()
        self._save_json(session_file, session_data)

        return session_data

    def destroy_session(self, session_id: str):
        """
        Destroy user session

        Args:
            session_id: Session ID
        """
        session_file = self.sessions_dir / f"session_{session_id}.json"
        if session_file.exists():
            session_data = self._load_json(session_file)
            if session_data:
                self.logger.log_access(session_data.get('email'), "logout")
            session_file.unlink()

        # Clear Flask session
        session.clear()

    def _load_json(self, path: Path) -> Optional[Dict[str, Any]]:
        """Load JSON file"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return None

    def _save_json(self, path: Path, data: Dict[str, Any]):
        """Save JSON file"""
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"Error saving session: {e}")


def login_required(f):
    """Decorator to require login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'session_id' not in session:
            return redirect(url_for('auth.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """Decorator to require admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'session_id' not in session:
            return redirect(url_for('auth.login', next=request.url))
        if not session.get('is_admin', False):
            return "Forbidden: Admin access required", 403
        return f(*args, **kwargs)
    return decorated_function
