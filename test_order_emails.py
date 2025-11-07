# Test Order Email Notifications
# Run this script to test if emails are being sent for orders

import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "covu.settings")
django.setup()

from orders.models import Order
from notifications.services import NotificationService

print("=" * 60)
print("TESTING ORDER EMAIL NOTIFICATIONS")
print("=" * 60)

# Get the most recent order
try:
    order = Order.objects.latest("created_at")
    print(f"\nFound order: {order.order_number}")
    print(f"Status: {order.status}")
    print(f"Buyer: {order.buyer.email}")
    print(f"Seller: {order.seller.email}")
    print(f"Product: {order.product.name}")

    # Test sending notification to seller
    print(f"\n{'=' * 60}")
    print("TESTING: Sending ORDER_CREATED notification to seller...")
    print(f"{'=' * 60}")

    notification = NotificationService.send_order_created_notification(
        seller=order.seller, order=order
    )

    print(f"\nNotification created: {notification.id}")
    print(f"Type: {notification.notification_type}")
    print(f"Sent: {notification.is_sent}")
    print(f"Delivery method: {notification.delivery_method}")
    print(f"Error (if any): {notification.error_message}")

    print(f"\n{'=' * 60}")
    print("Check your Celery worker terminal to see if email was queued!")
    print("Check the seller's email inbox for the notification!")
    print(f"{'=' * 60}\n")

except Order.DoesNotExist:
    print("\n❌ No orders found in database")
    print("Create an order first, then run this test\n")
except Exception as e:
    print(f"\n❌ Error: {str(e)}\n")
