"""
Example Usage of Notification Service

This file demonstrates how to use the NotificationService
in your order processing logic.

Copy these examples into your order service layer (orders/services.py)
when implementing the order flow.
"""

from notifications.services import NotificationService


# ==============================================================================
# EXAMPLE 1: Send notification when order is created
# ==============================================================================


def create_order_example(buyer, seller, product):
    """
    Example: Creating an order and notifying seller.
    """
    # ... your order creation logic ...

    # Create order (simplified)
    order = Order.objects.create(
        buyer=buyer,
        seller=seller,
        product=product,
        # ... other fields ...
    )

    # Send notification to seller
    notification = NotificationService.send_order_created_notification(
        seller=seller, order=order
    )

    print(f"✅ Notification sent to seller: {notification.title}")

    return order


# ==============================================================================
# EXAMPLE 2: Send notification when seller accepts order
# ==============================================================================


def accept_order_example(order):
    """
    Example: Seller accepts order, notify buyer.
    """
    # Update order status
    order.status = "ACCEPTED"
    order.accepted_at = timezone.now()
    order.save()

    # Send notification to buyer
    notification = NotificationService.send_order_accepted_notification(
        buyer=order.buyer, order=order
    )

    print(f"✅ Notification sent to buyer: {notification.title}")

    return order


# ==============================================================================
# EXAMPLE 3: Send notification when seller delivers
# ==============================================================================


def deliver_order_example(order):
    """
    Example: Seller marks order as delivered, notify buyer.
    """
    # Update order status
    order.status = "DELIVERED"
    order.delivered_at = timezone.now()
    order.save()

    # Send notification to buyer
    notification = NotificationService.send_order_delivered_notification(
        buyer=order.buyer, order=order
    )

    print(f"✅ Notification sent to buyer: {notification.title}")

    return order


# ==============================================================================
# EXAMPLE 4: Send notification when buyer confirms receipt
# ==============================================================================


def confirm_order_example(order):
    """
    Example: Buyer confirms receipt, notify seller about payment.
    """
    # Update order status
    order.status = "CONFIRMED"
    order.confirmed_at = timezone.now()
    order.save()

    # Release payment to seller (your escrow logic here)
    # ...

    # Send notification to seller
    notification = NotificationService.send_order_confirmed_notification(
        seller=order.seller, order=order
    )

    print(f"✅ Notification sent to seller: {notification.title}")

    return order


# ==============================================================================
# EXAMPLE 5: Send notification when order is cancelled
# ==============================================================================


def cancel_order_example(order, cancelled_by, reason):
    """
    Example: Order cancelled, notify both parties.

    Args:
        order: Order object
        cancelled_by: "BUYER" or "SELLER"
        reason: Cancellation reason string
    """
    # Update order status
    order.status = "CANCELLED"
    order.cancelled_at = timezone.now()
    order.cancelled_by = cancelled_by
    order.cancellation_reason = reason
    order.save()

    # Refund buyer (your escrow logic here)
    # ...

    # Notify both buyer and seller
    buyer_notification = NotificationService.send_order_cancelled_notification(
        user=order.buyer, order=order, cancelled_by=cancelled_by, reason=reason
    )

    seller_notification = NotificationService.send_order_cancelled_notification(
        user=order.seller, order=order, cancelled_by=cancelled_by, reason=reason
    )

    print(f"✅ Notification sent to buyer: {buyer_notification.title}")
    print(f"✅ Notification sent to seller: {seller_notification.title}")

    return order


# ==============================================================================
# EXAMPLE 6: Testing notifications in Django shell
# ==============================================================================

"""
# Open Django shell
python manage.py shell

# Import required models and service
from users.models import CustomUser
from orders.models import Order
from notifications.services import NotificationService

# Get test user and order
user = CustomUser.objects.first()
order = Order.objects.first()

# Test notification
notification = NotificationService.send_order_created_notification(
    seller=user,
    order=order
)

# Check notification in database
print(notification.title)
print(notification.message)
print(notification.is_sent)
print(notification.delivery_method)

# Check in admin panel
# http://127.0.0.1:8000/admin/notifications/notification/
"""


# ==============================================================================
# INTEGRATION WITH ORDER SERVICE LAYER
# ==============================================================================

"""
When you create your order service layer (orders/services.py),
integrate notifications like this:

from django.db import transaction
from notifications.services import NotificationService

class OrderService:
    
    @staticmethod
    def create_order(buyer, product, quantity=1):
        with transaction.atomic():
            # 1. Calculate delivery fee
            delivery_fee = calculate_delivery_fee(buyer, product.store)
            
            # 2. Validate wallet balance
            total = product.price + delivery_fee
            if buyer.wallet.balance < total:
                raise InsufficientFunds()
            
            # 3. Debit buyer wallet
            WalletTransaction.objects.create(
                wallet=buyer.wallet,
                transaction_type='DEBIT',
                amount=total,
                # ...
            )
            
            # 4. Create escrow
            escrow = EscrowTransaction.objects.create(
                # ...
            )
            
            # 5. Create order
            order = Order.objects.create(
                buyer=buyer,
                seller=product.store.seller,
                product=product,
                # ...
            )
            
            # 6. Send notification to seller
            NotificationService.send_order_created_notification(
                seller=product.store.seller,
                order=order
            )
            
            return order
"""
