# Test Order Cancellation Email
# Tests both buyer and seller cancellation scenarios

import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "covu.settings")
django.setup()

from orders.models import Order
from notifications.email_service import EmailNotificationService

print("=" * 70)
print("TESTING ORDER CANCELLATION EMAILS")
print("=" * 70)

# Get a pending order
try:
    order = Order.objects.filter(status="PENDING").first()

    if not order:
        print("\n❌ No pending orders found")
        print("Create an order first, then run this test\n")
        exit()

    print(f"\nUsing order: {order.order_number}")
    print(f"Buyer: {order.buyer.email}")
    print(f"Seller: {order.seller.email}")

    # Test 1: Seller cancels order
    print(f"\n{'=' * 70}")
    print("TEST 1: Seller Cancels Order → Buyer Receives Email")
    print(f"{'=' * 70}")

    order.cancelled_by = "SELLER"
    order.cancellation_reason = "Out of stock"

    EmailNotificationService.send_order_cancelled_to_buyer(
        order=order, reason=order.cancellation_reason
    )

    print(f"✅ Cancellation email sent to BUYER: {order.buyer.email}")
    print(f"   Message: Seller cancelled (refund mentioned)")

    # Test 2: Seller receives notification
    print(f"\n{'=' * 70}")
    print("TEST 2: Seller Cancels Order → Seller Receives Email")
    print(f"{'=' * 70}")

    EmailNotificationService.send_order_cancelled_to_seller(
        order=order, reason=order.cancellation_reason
    )

    print(f"✅ Cancellation email sent to SELLER: {order.seller.email}")
    print(f"   Message: You cancelled (NO refund mentioned)")

    # Test 3: Buyer cancels order
    print(f"\n{'=' * 70}")
    print("TEST 3: Buyer Cancels Order → Buyer Receives Email")
    print(f"{'=' * 70}")

    order.cancelled_by = "BUYER"
    order.cancellation_reason = "Changed my mind"

    EmailNotificationService.send_order_cancelled_to_buyer(
        order=order, reason=order.cancellation_reason
    )

    print(f"✅ Cancellation email sent to BUYER: {order.buyer.email}")
    print(f"   Message: You cancelled (refund mentioned)")

    # Test 4: Seller receives notification when buyer cancels
    print(f"\n{'=' * 70}")
    print("TEST 4: Buyer Cancels Order → Seller Receives Email")
    print(f"{'=' * 70}")

    EmailNotificationService.send_order_cancelled_to_seller(
        order=order, reason=order.cancellation_reason
    )

    print(f"✅ Cancellation email sent to SELLER: {order.seller.email}")
    print(f"   Message: Buyer cancelled (NO refund mentioned)")

    print(f"\n{'=' * 70}")
    print("✅ All cancellation email tests complete!")
    print("Check both buyer and seller email inboxes!")
    print(f"{'=' * 70}\n")

except Exception as e:
    print(f"\n❌ Error: {str(e)}\n")
