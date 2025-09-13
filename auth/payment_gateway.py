"""
Cryptomus payment gateway integration for Capsule AI
"""

import requests
import json
import hashlib
import hmac
from datetime import datetime
from typing import Optional, Dict, Tuple
import os


class CryptomusPaymentGateway:
    """Cryptomus payment gateway integration"""

    def __init__(self, merchant_id: str, api_key: str, test_mode: bool = True):
        self.merchant_id = merchant_id
        self.api_key = api_key
        self.test_mode = test_mode
        self.base_url = "https://api.cryptomus.com" if not test_mode else "https://api-sandbox.cryptomus.com"

    def create_payment(self, amount: float, currency: str = "USD",
                      credits_amount: int = 100) -> Tuple[bool, str, Optional[Dict]]:
        """Create a payment request"""
        try:
            payload = {
                "amount": str(amount),
                "currency": currency,
                "order_id": f"capsule_credits_{datetime.utcnow().timestamp()}",
                "url_return": "https://app.capsule-ai.com/payment/success",
                "url_callback": "https://api.capsule-ai.com/webhooks/cryptomus",
                "is_payment_multiple": False,
                "lifetime": 3600,  # 1 hour
                "additional_data": json.dumps({
                    "credits_amount": credits_amount,
                    "product": "Capsule AI Credits"
                })
            }

            headers = self._get_headers(payload)
            response = requests.post(
                f"{self.base_url}/v1/payment",
                json=payload,
                headers=headers
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("result"):
                    return True, "Payment created successfully", data["result"]
                else:
                    return False, data.get("message", "Payment creation failed"), None
            else:
                return False, f"HTTP {response.status_code}: {response.text}", None

        except Exception as e:
            return False, f"Payment creation error: {str(e)}", None

    def verify_payment(self, payment_data: Dict) -> bool:
        """Verify payment callback from Cryptomus"""
        try:
            # Verify webhook signature
            signature = payment_data.get("sign")
            if not signature:
                return False

            # Remove signature from data for verification
            data_to_verify = {k: v for k, v in payment_data.items() if k != "sign"}
            data_string = json.dumps(data_to_verify, separators=(',', ':'), sort_keys=True)

            expected_signature = hmac.new(
                self.api_key.encode(),
                data_string.encode(),
                hashlib.sha256
            ).hexdigest()

            return hmac.compare_digest(signature, expected_signature)

        except Exception:
            return False

    def get_payment_status(self, payment_id: str) -> Tuple[bool, str, Optional[Dict]]:
        """Get payment status"""
        try:
            payload = {"payment_id": payment_id}
            headers = self._get_headers(payload)

            response = requests.post(
                f"{self.base_url}/v1/payment/info",
                json=payload,
                headers=headers
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("result"):
                    return True, "Status retrieved successfully", data["result"]
                else:
                    return False, data.get("message", "Status retrieval failed"), None
            else:
                return False, f"HTTP {response.status_code}: {response.text}", None

        except Exception as e:
            return False, f"Status check error: {str(e)}", None

    def _get_headers(self, payload: Dict) -> Dict:
        """Generate headers for API requests"""
        data_string = json.dumps(payload, separators=(',', ':'), sort_keys=True)
        signature = hmac.new(
            self.api_key.encode(),
            data_string.encode(),
            hashlib.sha256
        ).hexdigest()

        return {
            "merchant": self.merchant_id,
            "sign": signature,
            "Content-Type": "application/json"
        }


class StripePaymentGateway:
    """Stripe payment gateway for fiat payments"""

    def __init__(self, api_key: str, webhook_secret: str):
        self.api_key = api_key
        self.webhook_secret = webhook_secret

    def create_payment_intent(self, amount: int, currency: str = "usd",
                             credits_amount: int = 100) -> Tuple[bool, str, Optional[Dict]]:
        """Create Stripe payment intent"""
        try:
            import stripe
            stripe.api_key = self.api_key

            intent = stripe.PaymentIntent.create(
                amount=amount,  # Amount in cents
                currency=currency,
                metadata={
                    "credits_amount": str(credits_amount),
                    "product": "Capsule AI Credits"
                }
            )

            return True, "Payment intent created", {
                "client_secret": intent.client_secret,
                "payment_intent_id": intent.id
            }

        except Exception as e:
            return False, f"Stripe error: {str(e)}", None

    def verify_webhook(self, payload: str, signature: str) -> bool:
        """Verify Stripe webhook signature"""
        try:
            import stripe
            stripe.WebhookSignature.verify_header(
                payload, signature, self.webhook_secret,
                tolerance=300  # 5 minutes
            )
            return True
        except Exception:
            return False


class PaymentManager:
    """Unified payment manager for multiple gateways"""

    def __init__(self):
        # Initialize payment gateways
        self.cryptomus = CryptomusPaymentGateway(
            merchant_id=os.getenv("CRYPTOMUS_MERCHANT_ID", ""),
            api_key=os.getenv("CRYPTOMUS_API_KEY", ""),
            test_mode=os.getenv("CRYPTOMUS_TEST_MODE", "true").lower() == "true"
        )

        self.stripe = StripePaymentGateway(
            api_key=os.getenv("STRIPE_API_KEY", ""),
            webhook_secret=os.getenv("STRIPE_WEBHOOK_SECRET", "")
        )

    def create_payment(self, amount: float, currency: str = "USD",
                      payment_method: str = "cryptomus", credits_amount: int = 100) -> Tuple[bool, str, Optional[Dict]]:
        """Create payment using specified method"""
        if payment_method == "cryptomus":
            return self.cryptomus.create_payment(amount, currency, credits_amount)
        elif payment_method == "stripe":
            # Convert amount to cents for Stripe
            amount_cents = int(amount * 100)
            return self.stripe.create_payment_intent(amount_cents, currency.lower(), credits_amount)
        else:
            return False, "Unsupported payment method", None

    def verify_payment(self, payment_method: str, payment_data: Dict) -> bool:
        """Verify payment from webhook"""
        if payment_method == "cryptomus":
            return self.cryptomus.verify_payment(payment_data)
        elif payment_method == "stripe":
            # Stripe verification would be handled differently
            return True  # Placeholder
        return False


# Pricing tiers
CREDIT_PACKAGES = {
    "starter": {"credits": 100, "price_usd": 10.00, "price_crypto": 0.00015},  # BTC equivalent
    "creator": {"credits": 250, "price_usd": 22.50, "price_crypto": 0.00035},
    "professional": {"credits": 500, "price_usd": 40.00, "price_crypto": 0.00065},
    "studio": {"credits": 1200, "price_usd": 90.00, "price_crypto": 0.0015},
    "enterprise": {"credits": 2500, "price_usd": 175.00, "price_crypto": 0.0030}
}

# Global payment manager instance
payment_manager = PaymentManager()