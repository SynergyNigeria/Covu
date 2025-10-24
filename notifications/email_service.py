"""
Email Notification Service for COVU Marketplace
Handles all email notifications for orders, wallets, and users
"""

from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class EmailNotificationService:
    """
    Centralized email notification service
    Sends email notifications for various marketplace events
    """

    @staticmethod
    def _send_email(
        subject: str, message: str, recipient_list: list, fail_silently: bool = True
    ):
        """
        Internal method to send emails with error handling

        Args:
            subject: Email subject
            message: Email body
            recipient_list: List of recipient email addresses
            fail_silently: Whether to suppress errors (default: True)
        """
        try:
            result = send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=recipient_list,
                fail_silently=fail_silently,
            )

            if result == 1:
                logger.info(f"Email sent successfully: {subject} to {recipient_list}")
                return True
            else:
                logger.warning(
                    f"Email may not have been sent: {subject} to {recipient_list}"
                )
                return False

        except Exception as e:
            logger.error(f"Error sending email '{subject}' to {recipient_list}: {e}")
            if not fail_silently:
                raise
            return False

    # ============================================================================
    # ORDER NOTIFICATIONS
    # ============================================================================

    @staticmethod
    def send_order_created_to_seller(order):
        """
        Notify seller when a new order is created

        Args:
            order: Order instance
        """
        subject = f"🛍️ New Order #{order.order_number} - COVU"

        message = f"""
Hi {order.seller.full_name},

Great news! You have a new order on COVU Marketplace.

📦 ORDER DETAILS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Order Number: #{order.order_number}
Amount: ₦{order.total_amount:,.2f}
Buyer: {order.buyer.full_name}
Items: {order.items.count()} product(s)
Status: Pending (Awaiting your acceptance)

🔔 ACTION REQUIRED:
Please log in to your COVU seller dashboard to review and accept this order.

👉 Login here: https://covu.ng/dashboard/orders/{order.id}

⏰ IMPORTANT: Please respond within 24 hours to maintain your seller rating.

Thank you for being a valued COVU seller!

Best regards,
The COVU Team

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
This is an automated message from COVU Marketplace.
For support: support@covu.ng
        """

        EmailNotificationService._send_email(
            subject=subject, message=message, recipient_list=[order.seller.email]
        )

    @staticmethod
    def send_order_accepted_to_buyer(order):
        """
        Notify buyer when seller accepts their order

        Args:
            order: Order instance
        """
        subject = f"✅ Order #{order.order_number} Accepted - COVU"

        message = f"""
Hi {order.buyer.full_name},

Good news! Your order has been accepted by the seller.

📦 ORDER DETAILS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Order Number: #{order.order_number}
Amount: ₦{order.total_amount:,.2f}
Seller: {order.seller.full_name}
Status: Accepted (Being prepared for delivery)

🎉 WHAT'S NEXT:
The seller is now preparing your order for delivery. You'll receive another 
notification once your order has been dispatched.

👉 Track your order: https://covu.ng/orders/{order.id}

💡 PAYMENT STATUS:
Your payment of ₦{order.total_amount:,.2f} is held securely in escrow and will 
be released to the seller only after you confirm receipt of your order.

Thank you for shopping on COVU!

Best regards,
The COVU Team

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
This is an automated message from COVU Marketplace.
For support: support@covu.ng
        """

        EmailNotificationService._send_email(
            subject=subject, message=message, recipient_list=[order.buyer.email]
        )

    @staticmethod
    def send_order_delivered_to_buyer(order):
        """
        Notify buyer when order is marked as delivered

        Args:
            order: Order instance
        """
        subject = f"📦 Order #{order.order_number} Delivered - COVU"

        message = f"""
Hi {order.buyer.full_name},

Your order has been delivered!

📦 ORDER DETAILS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Order Number: #{order.order_number}
Amount: ₦{order.total_amount:,.2f}
Seller: {order.seller.full_name}
Status: Delivered

🔔 IMPORTANT - ACTION REQUIRED:
Please confirm receipt of your order to release payment to the seller.

👉 Confirm delivery: https://covu.ng/orders/{order.id}/confirm

⚠️ BUYER PROTECTION:
• If you haven't received your order, DO NOT confirm delivery
• If there are any issues with your order, contact us immediately
• You have 48 hours to report any problems

💰 ESCROW REMINDER:
Your payment of ₦{order.total_amount:,.2f} is still held in escrow and will 
only be released to the seller after you confirm receipt.

Thank you for using COVU!

Best regards,
The COVU Team

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
This is an automated message from COVU Marketplace.
For support: support@covu.ng
        """

        EmailNotificationService._send_email(
            subject=subject, message=message, recipient_list=[order.buyer.email]
        )

    @staticmethod
    def send_order_confirmed_to_seller(order):
        """
        Notify seller when buyer confirms receipt and payment is released

        Args:
            order: Order instance
        """
        subject = f"💰 Payment Released - Order #{order.order_number} - COVU"

        message = f"""
Hi {order.seller.full_name},

Congratulations! Payment has been released for your order.

📦 ORDER DETAILS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Order Number: #{order.order_number}
Amount: ₦{order.total_amount:,.2f}
Buyer: {order.buyer.full_name}
Status: Completed ✅

💰 PAYMENT RELEASED:
₦{order.total_amount:,.2f} has been credited to your COVU wallet.

👉 View your wallet: https://covu.ng/dashboard/wallet
👉 Withdraw funds: https://covu.ng/dashboard/wallet/withdraw

⭐ NEXT STEP:
Encourage your buyer to leave a review to help build your seller reputation!

Thank you for being a valued COVU seller!

Best regards,
The COVU Team

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
This is an automated message from COVU Marketplace.
For support: support@covu.ng
        """

        EmailNotificationService._send_email(
            subject=subject, message=message, recipient_list=[order.seller.email]
        )

    @staticmethod
    def send_order_cancelled(
        order, recipient_email: str, recipient_name: str, reason: Optional[str] = None
    ):
        """
        Notify user when order is cancelled

        Args:
            order: Order instance
            recipient_email: Email address of recipient
            recipient_name: Name of recipient
            reason: Optional cancellation reason
        """
        subject = f"❌ Order #{order.order_number} Cancelled - COVU"

        reason_text = f"\n\nReason: {reason}" if reason else ""

        message = f"""
Hi {recipient_name},

Your order has been cancelled.{reason_text}

📦 ORDER DETAILS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Order Number: #{order.order_number}
Amount: ₦{order.total_amount:,.2f}
Status: Cancelled ❌

💰 REFUND INFORMATION:
If payment was made, a full refund of ₦{order.total_amount:,.2f} has been 
processed to your COVU wallet.

👉 View your wallet: https://covu.ng/dashboard/wallet
👉 View order details: https://covu.ng/orders/{order.id}

If you have any questions about this cancellation, please contact our support team.

Thank you for your understanding.

Best regards,
The COVU Team

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
This is an automated message from COVU Marketplace.
For support: support@covu.ng
        """

        EmailNotificationService._send_email(
            subject=subject, message=message, recipient_list=[recipient_email]
        )

    # ============================================================================
    # WALLET NOTIFICATIONS
    # ============================================================================

    @staticmethod
    def send_wallet_funded(user, amount: float, reference: str):
        """
        Notify user when wallet is funded successfully

        Args:
            user: User instance
            amount: Amount funded
            reference: Transaction reference
        """
        subject = f"💳 Wallet Funded - ₦{amount:,.2f} - COVU"

        message = f"""
Hi {user.full_name},

Your wallet has been funded successfully!

💰 TRANSACTION DETAILS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Amount: ₦{amount:,.2f}
Reference: {reference}
New Balance: ₦{user.wallet.balance:,.2f}
Status: Successful ✅

🎉 WHAT'S NEXT:
You can now use your wallet balance to:
• Purchase products on COVU Marketplace
• Pay for orders instantly
• Enjoy faster checkout

👉 View your wallet: https://covu.ng/dashboard/wallet
👉 Start shopping: https://covu.ng/products

Thank you for using COVU!

Best regards,
The COVU Team

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
This is an automated message from COVU Marketplace.
For support: support@covu.ng
        """

        EmailNotificationService._send_email(
            subject=subject, message=message, recipient_list=[user.email]
        )

    @staticmethod
    def send_withdrawal_initiated(
        user, amount: float, account_number: str, bank_name: str, reference: str
    ):
        """
        Notify user when withdrawal is initiated

        Args:
            user: User instance
            amount: Withdrawal amount
            account_number: Bank account number
            bank_name: Bank name
            reference: Transaction reference
        """
        subject = f"💸 Withdrawal Initiated - ₦{amount:,.2f} - COVU"

        message = f"""
Hi {user.full_name},

Your withdrawal request has been initiated.

💸 WITHDRAWAL DETAILS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Amount: ₦{amount:,.2f}
Account: {account_number} ({bank_name})
Reference: {reference}
Status: Processing ⏳

⏰ PROCESSING TIME:
Your funds should arrive in your bank account within 24 hours.

👉 Track withdrawal: https://covu.ng/dashboard/wallet/transactions

If you have any issues, please contact our support team.

Thank you for using COVU!

Best regards,
The COVU Team

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
This is an automated message from COVU Marketplace.
For support: support@covu.ng
        """

        EmailNotificationService._send_email(
            subject=subject, message=message, recipient_list=[user.email]
        )

    @staticmethod
    def send_withdrawal_completed(
        user, amount: float, account_number: str, bank_name: str, reference: str
    ):
        """
        Notify user when withdrawal is completed successfully

        Args:
            user: User instance
            amount: Withdrawal amount
            account_number: Bank account number
            bank_name: Bank name
            reference: Transaction reference
        """
        subject = f"✅ Withdrawal Completed - ₦{amount:,.2f} - COVU"

        message = f"""
Hi {user.full_name},

Your withdrawal has been completed successfully!

💸 WITHDRAWAL DETAILS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Amount: ₦{amount:,.2f}
Account: {account_number} ({bank_name})
Reference: {reference}
New Wallet Balance: ₦{user.wallet.balance:,.2f}
Status: Completed ✅

💰 FUNDS TRANSFERRED:
₦{amount:,.2f} has been successfully transferred to your bank account.
Please allow a few minutes for it to reflect in your account.

👉 View transaction history: https://covu.ng/dashboard/wallet/transactions

If you don't see the funds in your account within 24 hours, please contact 
your bank or our support team.

Thank you for using COVU!

Best regards,
The COVU Team

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
This is an automated message from COVU Marketplace.
For support: support@covu.ng
        """

        EmailNotificationService._send_email(
            subject=subject, message=message, recipient_list=[user.email]
        )

    @staticmethod
    def send_withdrawal_failed(user, amount: float, reference: str, reason: str):
        """
        Notify user when withdrawal fails

        Args:
            user: User instance
            amount: Withdrawal amount
            reference: Transaction reference
            reason: Failure reason
        """
        subject = f"⚠️ Withdrawal Failed - ₦{amount:,.2f} - COVU"

        message = f"""
Hi {user.full_name},

Unfortunately, your withdrawal request could not be processed.

💸 WITHDRAWAL DETAILS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Amount: ₦{amount:,.2f}
Reference: {reference}
Status: Failed ❌

⚠️ REASON:
{reason}

💰 FUNDS RETURNED:
₦{amount:,.2f} has been returned to your COVU wallet.
Your balance: ₦{user.wallet.balance:,.2f}

🔄 NEXT STEPS:
• Please verify your bank account details
• Try again with a smaller amount if the issue persists
• Contact our support team if you need assistance

👉 Try withdrawal again: https://covu.ng/dashboard/wallet/withdraw
👉 Update bank details: https://covu.ng/dashboard/settings

We apologize for the inconvenience.

Best regards,
The COVU Team

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
This is an automated message from COVU Marketplace.
For support: support@covu.ng
        """

        EmailNotificationService._send_email(
            subject=subject, message=message, recipient_list=[user.email]
        )

    # ============================================================================
    # USER NOTIFICATIONS
    # ============================================================================

    @staticmethod
    def send_welcome_email(user):
        """
        Send welcome email to new users

        Args:
            user: User instance
        """
        subject = "🎉 Welcome to COVU Marketplace!"

        message = f"""
Hi {user.full_name},

Welcome to COVU Marketplace! 🎉

We're excited to have you join our community of buyers and sellers.

🚀 GET STARTED:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
👉 Complete your profile: https://covu.ng/profile
👉 Browse products: https://covu.ng/products
👉 Set up your store: https://covu.ng/stores/create

💡 WHAT YOU CAN DO ON COVU:
• Buy products from verified sellers
• Sell your products to thousands of buyers
• Secure payments with escrow protection
• Fast and reliable transactions

🔒 SAFETY FIRST:
Your security is our priority. All transactions are protected by our 
secure escrow system, ensuring you only pay when you're satisfied.

Need help? Check out our FAQ or contact support@covu.ng

Happy buying and selling!

Best regards,
The COVU Team

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
This is an automated message from COVU Marketplace.
        """

        EmailNotificationService._send_email(
            subject=subject, message=message, recipient_list=[user.email]
        )

    @staticmethod
    def send_generic_notification(user, subject: str, message: str):
        """
        Send a generic notification email

        Args:
            user: User instance
            subject: Email subject
            message: Email message
        """
        EmailNotificationService._send_email(
            subject=subject, message=message, recipient_list=[user.email]
        )
