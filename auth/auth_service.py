"""
Authentication service for Capsule AI
"""

import jwt
import secrets
from datetime import datetime, timedelta
from typing import Optional, Tuple
from .models import User, db_manager


class AuthService:
    """Authentication service for user management"""

    def __init__(self, secret_key: Optional[str] = None, token_expiry_hours: int = 24):
        self.secret_key = secret_key or secrets.token_hex(32)
        self.token_expiry_hours = token_expiry_hours

    def register_user(self, email: str, password: str) -> Tuple[bool, str, Optional[User]]:
        """Register a new user"""
        if not self.validate_email(email):
            return False, "Invalid email format", None

        if not self.validate_password(password):
            return False, "Password must be at least 8 characters long", None

        # Check if user already exists
        existing_user = db_manager.get_user_by_email(email)
        if existing_user:
            return False, "Email already registered", None

        # Create new user
        user = db_manager.create_user(email, password)
        if user:
            return True, "Registration successful", user
        else:
            return False, "Registration failed", None

    def authenticate_user(self, email: str, password: str) -> Tuple[bool, str, Optional[User]]:
        """Authenticate user credentials"""
        user = db_manager.get_user_by_email(email)
        if not user:
            return False, "Invalid email or password", None

        if not db_manager.verify_password(password, user.password_hash):
            return False, "Invalid email or password", None

        # Update last login
        user.last_login = datetime.utcnow()
        db_manager.update_user(user)

        return True, "Authentication successful", user

    def generate_token(self, user: User) -> str:
        """Generate JWT token for user"""
        payload = {
            'user_id': user.user_id,
            'email': user.email,
            'exp': datetime.utcnow() + timedelta(hours=self.token_expiry_hours),
            'iat': datetime.utcnow()
        }
        return jwt.encode(payload, self.secret_key, algorithm='HS256')

    def verify_token(self, token: str) -> Optional[User]:
        """Verify JWT token and return user"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            user_id = payload.get('user_id')
            if user_id:
                return db_manager.get_user_by_id(user_id)
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
        return None

    def get_user_from_token(self, token: str) -> Optional[User]:
        """Get user from JWT token"""
        return self.verify_token(token)

    def deduct_credits(self, user: User, amount: int = 1) -> bool:
        """Deduct credits from user"""
        if user.deduct_credits(amount):
            db_manager.update_user(user)
            # Log usage
            db_manager.log_usage(
                user_id=user.user_id,
                action="generation",
                credits_used=amount,
                metadata={"type": "image_generation"}
            )
            return True
        return False

    def add_credits(self, user: User, amount: int, payment_method: str = "manual",
                   transaction_id: Optional[str] = None):
        """Add credits to user account"""
        user.add_credits(amount)
        db_manager.update_user(user)

        # Log payment
        with db_manager._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO payments (user_id, amount, credits_purchased,
                                    payment_method, transaction_id, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                user.user_id,
                amount * 0.1,  # Assuming $0.10 per credit
                amount,
                payment_method,
                transaction_id,
                "completed",
                datetime.utcnow().isoformat()
            ))
            conn.commit()

    def get_user_stats(self, user: User) -> dict:
        """Get user statistics"""
        usage_stats = db_manager.get_usage_stats(user.user_id)

        return {
            'credits_balance': user.credits_balance,
            'subscription_tier': user.subscription_tier,
            'total_credits_used': usage_stats['total_credits_used'],
            'usage_by_action': usage_stats['usage_by_action'],
            'member_since': user.created_at.isoformat() if user.created_at else None,
            'last_login': user.last_login.isoformat() if user.last_login else None
        }

    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

    @staticmethod
    def validate_password(password: str) -> bool:
        """Validate password strength"""
        return len(password) >= 8

    def reset_password(self, email: str) -> Tuple[bool, str]:
        """Initiate password reset (placeholder for email integration)"""
        user = db_manager.get_user_by_email(email)
        if user:
            # In a real implementation, send password reset email
            return True, "Password reset email sent"
        return False, "Email not found"

    def change_password(self, user: User, old_password: str, new_password: str) -> Tuple[bool, str]:
        """Change user password"""
        if not db_manager.verify_password(old_password, user.password_hash):
            return False, "Current password is incorrect"

        if not self.validate_password(new_password):
            return False, "New password must be at least 8 characters long"

        user.password_hash = db_manager.hash_password(new_password)
        db_manager.update_user(user)
        return True, "Password changed successfully"


# Global auth service instance
auth_service = AuthService()