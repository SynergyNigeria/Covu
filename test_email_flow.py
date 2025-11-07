# Complete Order Email Flow Test
# This tests all email notifications in the order lifecycle

import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "covu.settings")
django.setup()

from orders.models import Order
from notifications.models import Notification

print("=" * 70)
print("ORDER EMAIL NOTIFICATIONS - COMPLETE FLOW TEST")
print("=" * 70)

# Get all notifications sent in the last hour
from django.utils import timezone
from datetime import timedelta

one_hour_ago = timezone.now() - timedelta(hours=1)
recent_notifications = Notification.objects.filter(
    created_at__gte=one_hour_ago
).order_by("-created_at")

print(f"\n📊 Notifications sent in the last hour: {recent_notifications.count()}")
print("=" * 70)

for notif in recent_notifications:
    status_icon = "✅" if notif.is_sent else "❌"
    print(f"\n{status_icon} {notif.notification_type}")
    print(f"   To: {notif.user.email}")
    print(f"   Method: {notif.delivery_method}")
    print(f"   Order: #{notif.order.order_number if notif.order else 'N/A'}")
    print(f"   Sent: {notif.sent_at if notif.sent_at else 'Not sent'}")
    if notif.error_message:
        print(f"   Error: {notif.error_message}")

# Summary by type
print("\n" + "=" * 70)
print("NOTIFICATION SUMMARY BY TYPE:")
print("=" * 70)

from django.db.models import Count

summary = (
    Notification.objects.filter(created_at__gte=one_hour_ago)
    .values("notification_type", "delivery_method")
    .annotate(count=Count("id"))
    .order_by("notification_type")
)

for item in summary:
    print(
        f"{item['notification_type']:<20} | {item['delivery_method']:<10} | Count: {item['count']}"
    )

# Check pending orders
pending_orders = Order.objects.filter(status="PENDING").count()
print(f"\n📦 Pending Orders: {pending_orders}")

print("\n" + "=" * 70)
print("✅ Test Complete!")
print("Check seller and buyer email inboxes for notifications!")
print("=" * 70 + "\n")
