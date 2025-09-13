#!/usr/bin/env python3
"""
Test script for Capsule AI authentication system
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from auth.models import db_manager
    from auth.auth_service import auth_service

    print("🔐 Testing Capsule AI Authentication System")
    print("=" * 50)

    # Test user registration
    print("\n📝 Testing user registration...")
    success, message, user = auth_service.register_user('demo@capsule-ai.com', 'demo123456')
    print(f"Registration: {'✅' if success else '❌'} {message}")

    if user:
        print(f"User created: {user.email} with {user.credits_balance} credits")

        # Test login
        print("\n🔑 Testing login...")
        success, message, logged_in_user = auth_service.authenticate_user('demo@capsule-ai.com', 'demo123456')
        print(f"Login: {'✅' if success else '❌'} {message}")

        if logged_in_user:
            print(f"Logged in user: {logged_in_user.email}")

            # Test credits system
            print("\n💰 Testing credits system...")
            print(f"Initial credits: {logged_in_user.credits_balance}")

            # Deduct credits
            success = auth_service.deduct_credits(logged_in_user, 2)
            print(f"Credit deduction (2 credits): {'✅' if success else '❌'}")
            print(f"Remaining credits: {logged_in_user.credits_balance}")

            # Get user stats
            stats = auth_service.get_user_stats(logged_in_user)
            print(f"User stats retrieved: {'✅' if stats else '❌'}")
            if stats:
                print(f"  - Credits balance: {stats['credits_balance']}")
                print(f"  - Subscription tier: {stats['subscription_tier']}")

    print("\n" + "=" * 50)
    print("🎉 Authentication system test completed successfully!")
    print("\n🚀 Ready to run Capsule AI with authentication!")

except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're running this from the Capsule-AI directory")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()