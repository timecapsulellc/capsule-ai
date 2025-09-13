"""
Gradio UI components for Capsule AI authentication
"""

import gradio as gr
from typing import Optional, Callable
from .auth_service import auth_service
from .models import User


class AuthUI:
    """Authentication UI components for Gradio"""

    def __init__(self):
        self.current_user: Optional[User] = None
        self.on_auth_success: Optional[Callable] = None

    def create_login_tab(self):
        """Create login tab"""
        with gr.TabItem("🔐 Login", id="login_tab"):
            gr.Markdown("# Welcome to Capsule AI")
            gr.Markdown("*Transform your ideas into stunning visuals*")

            with gr.Row():
                with gr.Column():
                    email_input = gr.Textbox(
                        label="Email",
                        placeholder="your@email.com",
                        type="email"
                    )
                    password_input = gr.Textbox(
                        label="Password",
                        type="password",
                        placeholder="Enter your password"
                    )
                    login_btn = gr.Button("🚀 Login", variant="primary", size="lg")
                    register_link = gr.Markdown("[Don't have an account? Register here](#register)")

                with gr.Column():
                    gr.Markdown("### Why Choose Capsule AI?")
                    gr.Markdown("""
                    ✨ **Professional Quality**: Enterprise-grade AI image generation
                    ⚡ **Lightning Fast**: Generate images in seconds
                    💎 **Advanced Features**: Inpainting, outpainting, image prompting
                    🎨 **Creative Freedom**: 100+ artistic styles and models
                    🛡️ **Secure & Private**: Your data stays yours
                    """)

            login_status = gr.Textbox(
                label="Status",
                interactive=False,
                visible=False
            )

            def login_user(email, password):
                if not email or not password:
                    return "Please fill in all fields", gr.update(visible=False)

                success, message, user = auth_service.authenticate_user(email, password)
                if success and user:
                    self.current_user = user
                    if self.on_auth_success:
                        self.on_auth_success(user)
                    return f"✅ Welcome back, {user.email}!", gr.update(visible=True)
                else:
                    return f"❌ {message}", gr.update(visible=False)

            login_btn.click(
                login_user,
                inputs=[email_input, password_input],
                outputs=[login_status, gr.update(visible=True)]
            )

    def create_register_tab(self):
        """Create registration tab"""
        with gr.TabItem("📝 Register", id="register_tab"):
            gr.Markdown("# Join Capsule AI")
            gr.Markdown("*Start creating with 50 free credits*")

            with gr.Row():
                with gr.Column():
                    reg_email = gr.Textbox(
                        label="Email",
                        placeholder="your@email.com",
                        type="email"
                    )
                    reg_password = gr.Textbox(
                        label="Password",
                        type="password",
                        placeholder="At least 8 characters"
                    )
                    reg_confirm_password = gr.Textbox(
                        label="Confirm Password",
                        type="password",
                        placeholder="Repeat your password"
                    )
                    register_btn = gr.Button("🎨 Create Account", variant="primary", size="lg")
                    login_link = gr.Markdown("[Already have an account? Login here](#login)")

                with gr.Column():
                    gr.Markdown("### Free Tier Benefits")
                    gr.Markdown("""
                    🎁 **50 Free Credits**: Start creating immediately
                    🎯 **Full Access**: All generation features available
                    ⚡ **No Watermark**: High-quality outputs
                    📊 **Usage Tracking**: Monitor your creations
                    🔄 **Upgrade Anytime**: Seamless plan upgrades
                    """)

            register_status = gr.Textbox(
                label="Status",
                interactive=False,
                visible=False
            )

            def register_user(email, password, confirm_password):
                if not email or not password or not confirm_password:
                    return "Please fill in all fields", gr.update(visible=False)

                if password != confirm_password:
                    return "Passwords do not match", gr.update(visible=False)

                success, message, user = auth_service.register_user(email, password)
                if success and user:
                    return f"✅ Account created successfully! Welcome to Capsule AI, {user.email}!", gr.update(visible=True)
                else:
                    return f"❌ {message}", gr.update(visible=False)

            register_btn.click(
                register_user,
                inputs=[reg_email, reg_password, reg_confirm_password],
                outputs=[register_status, gr.update(visible=True)]
            )

    def create_dashboard_tab(self):
        """Create user dashboard tab"""
        with gr.TabItem("📊 Dashboard", id="dashboard_tab"):
            gr.Markdown("# Your Capsule AI Dashboard")

            with gr.Row():
                with gr.Column(scale=1):
                    credits_display = gr.Textbox(
                        label="Credits Balance",
                        value="Please login to view",
                        interactive=False
                    )
                    tier_display = gr.Textbox(
                        label="Subscription Tier",
                        value="Please login to view",
                        interactive=False
                    )

                with gr.Column(scale=2):
                    usage_stats = gr.JSON(
                        label="Usage Statistics",
                        value={"message": "Please login to view usage statistics"}
                    )

            refresh_btn = gr.Button("🔄 Refresh Dashboard", variant="secondary")

            def update_dashboard():
                if not self.current_user:
                    return "Please login first", "Please login first", {"message": "Please login to view statistics"}

                stats = auth_service.get_user_stats(self.current_user)
                return (
                    f"{stats['credits_balance']} credits",
                    stats['subscription_tier'].title(),
                    stats
                )

            refresh_btn.click(
                update_dashboard,
                outputs=[credits_display, tier_display, usage_stats]
            )

    def create_purchase_tab(self):
        """Create credits purchase tab"""
        with gr.TabItem("💰 Buy Credits", id="purchase_tab"):
            gr.Markdown("# Purchase Credits")

            with gr.Row():
                with gr.Column():
                    gr.Markdown("### Credit Packages")

                    # Credit package buttons would go here
                    starter_btn = gr.Button("🎯 Starter: 100 Credits - $10", variant="secondary")
                    creator_btn = gr.Button("🎨 Creator: 250 Credits - $22.50", variant="secondary")
                    pro_btn = gr.Button("⚡ Professional: 500 Credits - $40", variant="primary")
                    studio_btn = gr.Button("🏢 Studio: 1200 Credits - $90", variant="secondary")

                with gr.Column():
                    gr.Markdown("### Payment Methods")
                    payment_method = gr.Radio(
                        choices=["💳 Credit Card", "₿ Cryptocurrency", "🏦 Bank Transfer"],
                        label="Select Payment Method",
                        value="💳 Credit Card"
                    )

                    gr.Markdown("### Secure Payment Processing")
                    gr.Markdown("""
                    🔒 **256-bit SSL Encryption**
                    🛡️ **PCI DSS Compliant**
                    ⚡ **Instant Credit Delivery**
                    💯 **Money-back Guarantee**
                    """)

            purchase_status = gr.Textbox(
                label="Purchase Status",
                interactive=False,
                visible=False
            )

            def process_purchase(package, payment_method):
                if not self.current_user:
                    return "Please login first"

                # This would integrate with the payment gateway
                return f"Processing {package} payment via {payment_method}..."

            starter_btn.click(
                lambda: process_purchase("Starter", payment_method.value),
                outputs=purchase_status
            )
            creator_btn.click(
                lambda: process_purchase("Creator", payment_method.value),
                outputs=purchase_status
            )
            pro_btn.click(
                lambda: process_purchase("Professional", payment_method.value),
                outputs=purchase_status
            )
            studio_btn.click(
                lambda: process_purchase("Studio", payment_method.value),
                outputs=purchase_status
            )

    def create_auth_interface(self, on_auth_success: Optional[Callable] = None):
        """Create the complete authentication interface"""
        self.on_auth_success = on_auth_success

        with gr.Tabs() as auth_tabs:
            self.create_login_tab()
            self.create_register_tab()
            self.create_dashboard_tab()
            self.create_purchase_tab()

        return auth_tabs

    def get_current_user(self) -> Optional[User]:
        """Get currently authenticated user"""
        return self.current_user

    def logout(self):
        """Logout current user"""
        self.current_user = None
        return "Logged out successfully"


# Global auth UI instance
auth_ui = AuthUI()