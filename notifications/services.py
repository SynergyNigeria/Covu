"""
Notification Service Layer for COVU Marketplace.

This module handles all notification logic for the platform.

Current Implementation: Email notifications + Console logging
Future: WhatsApp Business API integration

When WhatsApp API is ready, update the _send_via_whatsapp() method
with actual API calls.
"""

from django.utils import timezone
from django.conf import settings
from .models import Notification
from .email_service import EmailNotificationService
import logging

logger = logging.getLogger(__name__)


# ==============================================================================
# NOTIFICATION SERVICE
# ==============================================================================


class NotificationService:
    """
    Service for sending notifications to users.

    All notification methods follow the same pattern:
    1. Create Notification record in database
    2. Send via configured method (currently console)
    3. Update delivery status
    4. Return notification object
    """

    @staticmethod
    def send_order_created_notification(seller, order):
        """
        Notify seller that a new order has been placed.

        Args:
            seller: User object (seller)
            order: Order object

        Returns:
            Notification object
        """
        title = f"New Order #{order.order_number}"
        message = (
            f"🛍️ NEW ORDER RECEIVED!\n\n"
            f"Order: #{order.order_number}\n"
            f"Product: {order.product.name}\n"
            f"Price: ₦{order.product_price:,.2f}\n"
            f"Delivery Fee: ₦{order.delivery_fee:,.2f}\n"
            f"Total: ₦{order.total_amount:,.2f}\n\n"
            f"📍 DELIVERY INSTRUCTIONS:\n{order.delivery_message}\n\n"
            f"Buyer: {order.buyer.get_full_name()}\n"
            f"Phone: {order.buyer.phone_number}\n"
            f"Location: {order.buyer.city}, {order.buyer.get_state_display()}\n\n"
            f"⚡ Please accept or reject this order in your dashboard."
        )

        return NotificationService._create_and_send(
            user=seller,
            notification_type="ORDER_CREATED",
            title=title,
            message=message,
            order=order,
        )

    @staticmethod
    def send_order_accepted_notification(buyer, order):
        """
        Notify buyer that seller accepted their order.

        Args:
            buyer: User object (buyer)
            order: Order object

        Returns:
            Notification object
        """
        title = f"Order #{order.order_number} Accepted"
        message = (
            f"✅ ORDER ACCEPTED!\n\n"
            f"Order: #{order.order_number}\n"
            f"Product: {order.product.name}\n"
            f"Store: {order.product.store.name}\n\n"
            f"Your order has been accepted by the seller.\n"
            f"The seller is now preparing your item for delivery.\n\n"
            f"💰 Your payment of ₦{order.total_amount:,.2f} is safely held in escrow.\n"
            f"📦 You will be notified when the seller delivers."
        )

        return NotificationService._create_and_send(
            user=buyer,
            notification_type="ORDER_ACCEPTED",
            title=title,
            message=message,
            order=order,
        )

    @staticmethod
    def send_order_delivered_notification(buyer, order):
        """
        Notify buyer that seller has delivered the order.

        Args:
            buyer: User object (buyer)
            order: Order object

        Returns:
            Notification object
        """
        title = f"Order #{order.order_number} Delivered"
        message = (
            f"📦 ORDER DELIVERED!\n\n"
            f"Order: #{order.order_number}\n"
            f"Product: {order.product.name}\n"
            f"Store: {order.product.store.name}\n\n"
            f"The seller has marked this order as DELIVERED.\n\n"
            f"⚠️ IMPORTANT: Please confirm that you have received your item.\n"
            f"- If received and satisfied: Confirm delivery in your dashboard\n"
            f"- If NOT received: Contact us immediately\n\n"
            f"💡 The seller will only be paid after you confirm receipt."
        )

        return NotificationService._create_and_send(
            user=buyer,
            notification_type="ORDER_DELIVERED",
            title=title,
            message=message,
            order=order,
        )

    @staticmethod
    def send_order_confirmed_notification(seller, order):
        """
        Notify seller that buyer confirmed receipt.

        Args:
            seller: User object (seller)
            order: Order object

        Returns:
            Notification object
        """
        title = f"Order #{order.order_number} Confirmed"
        message = (
            f"🎉 ORDER CONFIRMED!\n\n"
            f"Order: #{order.order_number}\n"
            f"Product: {order.product.name}\n"
            f"Amount: ₦{order.total_amount:,.2f}\n\n"
            f"The buyer has confirmed receipt of the item.\n"
            f"✅ Payment of ₦{order.total_amount:,.2f} has been credited to your wallet.\n\n"
            f"💰 Current Wallet Balance: ₦{seller.wallet.balance:,.2f}\n\n"
            f"Thank you for selling on COVU!"
        )

        return NotificationService._create_and_send(
            user=seller,
            notification_type="PAYMENT_RECEIVED",
            title=title,
            message=message,
            order=order,
        )

    @staticmethod
    def send_order_cancelled_notification(user, order, cancelled_by, reason):
        """
        Notify user that order was cancelled.

        Args:
            user: User object (buyer or seller)
            order: Order object
            cancelled_by: "BUYER" or "SELLER"
            reason: Cancellation reason

        Returns:
            Notification object
        """
        is_buyer = user == order.buyer
        title = f"Order #{order.order_number} Cancelled"

        if is_buyer:
            # Notification to buyer
            if cancelled_by == "BUYER":
                message = (
                    f"✓ ORDER CANCELLED\n\n"
                    f"Order: #{order.order_number}\n"
                    f"Product: {order.product.name}\n\n"
                    f"You cancelled this order.\n"
                    f"Reason: {reason}\n\n"
                    f"💰 Refund of ₦{order.total_amount:,.2f} has been issued to your wallet.\n"
                    f"💡 Current Wallet Balance: ₦{user.wallet.balance:,.2f}"
                )
            else:
                message = (
                    f"❌ ORDER CANCELLED BY SELLER\n\n"
                    f"Order: #{order.order_number}\n"
                    f"Product: {order.product.name}\n\n"
                    f"The seller cancelled this order.\n"
                    f"Reason: {reason}\n\n"
                    f"💰 Full refund of ₦{order.total_amount:,.2f} has been issued to your wallet.\n"
                    f"💡 Current Wallet Balance: ₦{user.wallet.balance:,.2f}\n\n"
                    f"We apologize for the inconvenience."
                )
        else:
            # Notification to seller
            if cancelled_by == "SELLER":
                message = (
                    f"✓ ORDER CANCELLED\n\n"
                    f"Order: #{order.order_number}\n"
                    f"Product: {order.product.name}\n\n"
                    f"You cancelled this order.\n"
                    f"Reason: {reason}\n\n"
                    f"The buyer has been refunded ₦{order.total_amount:,.2f}."
                )
            else:
                message = (
                    f"❌ ORDER CANCELLED BY BUYER\n\n"
                    f"Order: #{order.order_number}\n"
                    f"Product: {order.product.name}\n\n"
                    f"The buyer cancelled this order.\n"
                    f"Reason: {reason}\n\n"
                    f"The buyer has been refunded ₦{order.total_amount:,.2f}."
                )

        return NotificationService._create_and_send(
            user=user,
            notification_type="ORDER_CANCELLED",
            title=title,
            message=message,
            order=order,
        )

    @staticmethod
    def _create_and_send(user, notification_type, title, message, order=None):
        """
        Internal method to create notification and attempt delivery.

        Args:
            user: User object
            notification_type: Notification type (from NOTIFICATION_TYPES)
            title: Notification title
            message: Notification message
            order: Order object (optional)

        Returns:
            Notification object
        """
        # Create notification record
        notification = Notification.objects.create(
            user=user,
            notification_type=notification_type,
            title=title,
            message=message,
            order=order,
        )

        # Attempt to send
        try:
            NotificationService._send_notification(notification)
            notification.is_sent = True
            notification.sent_at = timezone.now()
            notification.save()
        except Exception as e:
            notification.error_message = str(e)
            notification.save()
            logger.error(f"Failed to send notification {notification.id}: {str(e)}")

        return notification

    @staticmethod
    def _send_notification(notification):
        """
        Send notification via configured method.

        Current: Email notifications (async via Celery)
        Future: WhatsApp Business API

        Args:
            notification: Notification object
        """
        # Send email notification asynchronously
        NotificationService._send_via_email(notification)

        # Console logging only in DEBUG mode (for monitoring, not delivery)
        if settings.DEBUG:
            NotificationService._log_to_console(notification)

        # TODO: When WhatsApp API ready, add WhatsApp notification
        # NotificationService._send_via_whatsapp(notification)

    @staticmethod
    def _send_via_email(notification):
        """
        Send notification via email using Celery async tasks.

        Args:
            notification: Notification object
        """
        try:
            from .tasks import send_order_notification_email_task

            # Send email asynchronously using Celery
            send_order_notification_email_task.delay(
                notification_type=notification.notification_type,
                order_id=str(notification.order.id) if notification.order else None,
                user_id=notification.user.id,
            )

            notification.delivery_method = "EMAIL"
            notification.save()  # Save delivery method immediately
            logger.info(
                f"Email notification queued for async sending: {notification.notification_type}"
            )

        except Exception as e:
            logger.error(f"Failed to queue email notification: {str(e)}")
            # Fallback: Try sending synchronously
            try:
                from .email_service import EmailNotificationService

                # Route to appropriate email method based on notification type
                if notification.notification_type == "ORDER_CREATED":
                    EmailNotificationService.send_order_created_to_seller(
                        notification.order
                    )
                elif notification.notification_type == "ORDER_ACCEPTED":
                    EmailNotificationService.send_order_accepted_to_buyer(
                        notification.order
                    )
                elif notification.notification_type == "ORDER_DELIVERED":
                    EmailNotificationService.send_order_delivered_to_buyer(
                        notification.order
                    )
                elif notification.notification_type == "PAYMENT_RECEIVED":
                    EmailNotificationService.send_order_confirmed_to_seller(
                        notification.order
                    )
                elif notification.notification_type == "ORDER_CANCELLED":
                    if notification.user == notification.order.buyer:
                        EmailNotificationService.send_order_cancelled_to_buyer(
                            order=notification.order,
                            reason=notification.order.cancellation_reason,
                        )
                    else:
                        EmailNotificationService.send_order_cancelled_to_seller(
                            order=notification.order,
                            reason=notification.order.cancellation_reason,
                        )

                notification.delivery_method = "EMAIL"
                notification.save()  # Save after sync send
                logger.info(
                    f"Email sent synchronously (fallback): {notification.notification_type}"
                )

            except Exception as fallback_error:
                logger.error(
                    f"Fallback email sending also failed: {str(fallback_error)}"
                )
                notification.delivery_method = "CONSOLE"
                notification.save()  # Save console fallback

    @staticmethod
    def _log_to_console(notification):
        """
        Log notification to console for debugging (does NOT set delivery method).

        Args:
            notification: Notification object
        """
        print("\n" + "=" * 60)
        print(f"📱 NOTIFICATION TO: {notification.user.email}")
        print(f"📞 Phone: {notification.user.phone_number}")
        print("=" * 60)
        print(f"TITLE: {notification.title}")
        print("-" * 60)
        print(notification.message)
        print("=" * 60 + "\n")

    @staticmethod
    def _send_via_whatsapp(notification):
        """
        TODO: Send notification via WhatsApp Business API.

        This method will be implemented when WhatsApp API credentials are ready.

        Implementation steps:
        1. Format message for WhatsApp
        2. Call WhatsApp Business API
        3. Handle response/errors
        4. Update notification.delivery_method = "WHATSAPP"

        Args:
            notification: Notification object
        """
        # TODO: Implement WhatsApp Business API integration
        # Example structure:
        #
        # import requests
        #
        # url = settings.WHATSAPP_API_URL
        # headers = {
        #     "Authorization": f"Bearer {settings.WHATSAPP_API_TOKEN}",
        #     "Content-Type": "application/json"
        # }
        # data = {
        #     "messaging_product": "whatsapp",
        #     "to": notification.user.phone_number,
        #     "type": "text",
        #     "text": {
        #         "body": notification.message
        #     }
        # }
        #
        # response = requests.post(url, json=data, headers=headers)
        # response.raise_for_status()
        #
        # notification.delivery_method = "WHATSAPP"

        raise NotImplementedError(
            "WhatsApp integration not yet implemented. "
            "Update this method when WhatsApp API credentials are ready."
        )
