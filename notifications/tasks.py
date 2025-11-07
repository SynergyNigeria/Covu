"""
Celery tasks for asynchronous email sending
"""

from celery import shared_task
from celery.utils.log import get_task_logger
from django.core.mail import send_mail
from django.conf import settings

logger = get_task_logger(__name__)


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={
        "max_retries": 3,
        "countdown": 60,
    },  # Retry 3 times, wait 60s between retries
    retry_backoff=True,  # Exponential backoff
    retry_jitter=True,  # Add randomness to avoid thundering herd
)
def send_email_task(self, subject, message, recipient_list, from_email=None):
    """
    Async task to send email with retry logic

    Args:
        subject: Email subject
        message: Email body
        recipient_list: List of recipient emails
        from_email: Optional from email (defaults to DEFAULT_FROM_EMAIL)

    Returns:
        int: Number of emails sent (1 on success, 0 on failure)
    """
    try:
        from_email = from_email or settings.DEFAULT_FROM_EMAIL

        result = send_mail(
            subject=subject,
            message=message,
            from_email=from_email,
            recipient_list=recipient_list,
            fail_silently=False,  # Raise exception on failure for retry
        )

        logger.info(f"Email sent successfully: {subject} to {recipient_list}")
        return result

    except Exception as exc:
        logger.error(
            f"Failed to send email: {subject} to {recipient_list}. Error: {str(exc)}"
        )
        # Re-raise for Celery to handle retry
        raise self.retry(exc=exc)


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 3, "countdown": 60},
    retry_backoff=True,
    retry_jitter=True,
)
def send_order_notification_email_task(self, notification_type, order_id, user_id):
    """
    Async task to send order-related emails

    Args:
        notification_type: Type of notification (ORDER_CREATED, ORDER_ACCEPTED, etc.)
        order_id: UUID of the order
        user_id: ID of the user to notify

    Returns:
        bool: True if email sent successfully
    """
    try:
        from orders.models import Order
        from users.models import CustomUser
        from notifications.email_service import EmailNotificationService

        order = Order.objects.get(id=order_id)
        user = CustomUser.objects.get(id=user_id)

        # Route to appropriate email method
        if notification_type == "ORDER_CREATED":
            EmailNotificationService.send_order_created_to_seller(order)

        elif notification_type == "ORDER_ACCEPTED":
            EmailNotificationService.send_order_accepted_to_buyer(order)

        elif notification_type == "ORDER_DELIVERED":
            EmailNotificationService.send_order_delivered_to_buyer(order)

        elif notification_type == "PAYMENT_RECEIVED":
            EmailNotificationService.send_order_confirmed_to_seller(order)

        elif notification_type == "ORDER_CANCELLED":
            # Determine if user is buyer or seller and send appropriate email
            if user.id == order.buyer.id:
                EmailNotificationService.send_order_cancelled_to_buyer(
                    order=order,
                    reason=order.cancellation_reason,
                )
            else:
                EmailNotificationService.send_order_cancelled_to_seller(
                    order=order,
                    reason=order.cancellation_reason,
                )

        logger.info(
            f"Order notification sent: {notification_type} for order {order_id}"
        )
        return True

    except Exception as exc:
        logger.error(
            f"Failed to send order notification: {notification_type} for order {order_id}. Error: {str(exc)}"
        )
        raise self.retry(exc=exc)


@shared_task
def send_bulk_emails_task(subject, message, recipient_list, from_email=None):
    """
    Send emails to multiple recipients (marketing, announcements, etc.)

    Args:
        subject: Email subject
        message: Email body
        recipient_list: List of recipient emails
        from_email: Optional from email

    Returns:
        dict: Summary of sent/failed emails
    """
    from_email = from_email or settings.DEFAULT_FROM_EMAIL
    sent_count = 0
    failed_count = 0

    for recipient in recipient_list:
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=from_email,
                recipient_list=[recipient],
                fail_silently=False,
            )
            sent_count += 1
            logger.info(f"Bulk email sent to: {recipient}")

        except Exception as e:
            failed_count += 1
            logger.error(f"Failed to send bulk email to {recipient}: {str(e)}")

    result = {
        "sent": sent_count,
        "failed": failed_count,
        "total": len(recipient_list),
    }

    logger.info(f"Bulk email task complete: {result}")
    return result
