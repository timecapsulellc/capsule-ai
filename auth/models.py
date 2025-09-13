"""
User models and database management for Capsule AI
"""

import sqlite3
import json
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import os


class User:
    """User model for Capsule AI"""

    def __init__(self, user_id: str, email: str, password_hash: str,
                 credits_balance: int = 50, subscription_tier: str = "free",
                 created_at: Optional[datetime] = None,
                 last_login: Optional[datetime] = None,
                 is_active: bool = True):
        self.user_id = user_id
        self.email = email
        self.password_hash = password_hash
        self.credits_balance = credits_balance
        self.subscription_tier = subscription_tier
        self.created_at = created_at or datetime.utcnow()
        self.last_login = last_login
        self.is_active = is_active

    @classmethod
    def from_dict(cls, data: Dict) -> 'User':
        """Create User instance from dictionary"""
        return cls(
            user_id=data['user_id'],
            email=data['email'],
            password_hash=data['password_hash'],
            credits_balance=data.get('credits_balance', 50),
            subscription_tier=data.get('subscription_tier', 'free'),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else None,
            last_login=datetime.fromisoformat(data['last_login']) if data.get('last_login') else None,
            is_active=data.get('is_active', True)
        )

    def to_dict(self) -> Dict:
        """Convert User instance to dictionary"""
        return {
            'user_id': self.user_id,
            'email': self.email,
            'password_hash': self.password_hash,
            'credits_balance': self.credits_balance,
            'subscription_tier': self.subscription_tier,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'is_active': self.is_active
        }

    def has_credits(self, amount: int = 1) -> bool:
        """Check if user has sufficient credits"""
        return self.credits_balance >= amount

    def deduct_credits(self, amount: int) -> bool:
        """Deduct credits from user balance"""
        if self.has_credits(amount):
            self.credits_balance -= amount
            return True
        return False

    def add_credits(self, amount: int):
        """Add credits to user balance"""
        self.credits_balance += amount


class DatabaseManager:
    """SQLite database manager for user data"""

    def __init__(self, db_path: str = "capsule_ai.db"):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Initialize database tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    credits_balance INTEGER DEFAULT 50,
                    subscription_tier TEXT DEFAULT 'free',
                    created_at TEXT NOT NULL,
                    last_login TEXT,
                    is_active BOOLEAN DEFAULT 1
                )
            ''')

            # Usage logs table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS usage_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    credits_used INTEGER DEFAULT 0,
                    metadata TEXT,
                    timestamp TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')

            # Payments table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS payments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    amount REAL NOT NULL,
                    currency TEXT DEFAULT 'USD',
                    credits_purchased INTEGER NOT NULL,
                    payment_method TEXT,
                    transaction_id TEXT,
                    status TEXT DEFAULT 'pending',
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')

            conn.commit()

    def create_user(self, email: str, password: str) -> Optional[User]:
        """Create a new user"""
        try:
            user_id = secrets.token_hex(16)
            password_hash = self.hash_password(password)
            created_at = datetime.utcnow()

            user = User(
                user_id=user_id,
                email=email,
                password_hash=password_hash,
                credits_balance=50,  # Free tier credits
                subscription_tier="free",
                created_at=created_at
            )

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO users (user_id, email, password_hash, credits_balance,
                                     subscription_tier, created_at, is_active)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    user.user_id, user.email, user.password_hash, user.credits_balance,
                    user.subscription_tier, user.created_at.isoformat(), user.is_active
                ))
                conn.commit()

            return user
        except sqlite3.IntegrityError:
            return None  # Email already exists

    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE email = ? AND is_active = 1', (email,))
            row = cursor.fetchone()

            if row:
                user_data = {
                    'user_id': row[0],
                    'email': row[1],
                    'password_hash': row[2],
                    'credits_balance': row[3],
                    'subscription_tier': row[4],
                    'created_at': row[5],
                    'last_login': row[6],
                    'is_active': bool(row[7])
                }
                return User.from_dict(user_data)
        return None

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE user_id = ? AND is_active = 1', (user_id,))
            row = cursor.fetchone()

            if row:
                user_data = {
                    'user_id': row[0],
                    'email': row[1],
                    'password_hash': row[2],
                    'credits_balance': row[3],
                    'subscription_tier': row[4],
                    'created_at': row[5],
                    'last_login': row[6],
                    'is_active': bool(row[7])
                }
                return User.from_dict(user_data)
        return None

    def update_user(self, user: User):
        """Update user information"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE users SET
                    credits_balance = ?,
                    subscription_tier = ?,
                    last_login = ?,
                    is_active = ?
                WHERE user_id = ?
            ''', (
                user.credits_balance,
                user.subscription_tier,
                user.last_login.isoformat() if user.last_login else None,
                user.is_active,
                user.user_id
            ))
            conn.commit()

    def log_usage(self, user_id: str, action: str, credits_used: int = 0, metadata: Optional[Dict] = None):
        """Log user usage"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO usage_logs (user_id, action, credits_used, metadata, timestamp)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                user_id,
                action,
                credits_used,
                json.dumps(metadata) if metadata else None,
                datetime.utcnow().isoformat()
            ))
            conn.commit()

    def get_usage_stats(self, user_id: str, days: int = 30) -> Dict:
        """Get usage statistics for user"""
        cutoff_date = (datetime.utcnow() - timedelta(days=days)).isoformat()

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Total credits used
            cursor.execute('''
                SELECT SUM(credits_used) FROM usage_logs
                WHERE user_id = ? AND timestamp >= ?
            ''', (user_id, cutoff_date))
            total_credits = cursor.fetchone()[0] or 0

            # Usage by action
            cursor.execute('''
                SELECT action, SUM(credits_used), COUNT(*)
                FROM usage_logs
                WHERE user_id = ? AND timestamp >= ?
                GROUP BY action
            ''', (user_id, cutoff_date))

            usage_by_action = {}
            for row in cursor.fetchall():
                usage_by_action[row[0]] = {
                    'credits_used': row[1],
                    'count': row[2]
                }

            return {
                'total_credits_used': total_credits,
                'usage_by_action': usage_by_action,
                'period_days': days
            }

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using SHA-256 with salt"""
        salt = secrets.token_hex(16)
        password_hash = hashlib.sha256(f"{salt}{password}".encode()).hexdigest()
        return f"{salt}:{password_hash}"

    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """Verify password against hash"""
        try:
            salt, hash_value = password_hash.split(':')
            computed_hash = hashlib.sha256(f"{salt}{password}".encode()).hexdigest()
            return computed_hash == hash_value
        except ValueError:
            return False


# Global database instance
db_manager = DatabaseManager()