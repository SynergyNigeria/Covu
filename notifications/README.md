# Notifications App - COVU Marketplace

> **Status**: ✅ Ready (Placeholder Implementation)  
> **WhatsApp Integration**: ⏳ Pending (When API credentials ready)

---

## 📋 Overview

The notifications app handles all user notifications in the COVU marketplace. It provides a clean, production-ready structure with **placeholder console logging** that can be easily upgraded to **WhatsApp Business API** when credentials are available.

### Current Implementation

- ✅ **Notification Model** - Stores all notification history in database
- ✅ **NotificationService** - Clean service layer for sending notifications
- ✅ **Console Logging** - Placeholder that prints to console
- ✅ **Admin Interface** - View all notifications with color-coded status
- ✅ **Complete Message Templates** - All notification types ready

### Future Implementation (When WhatsApp API Ready)

- ⏳ **WhatsApp Business API Integration** - Just update `_send_via_whatsapp()` method
- ⏳ **Message Templates** - Already prepared, just need API formatting
- ⏳ **Delivery Confirmation** - Track WhatsApp delivery status

---

## 🎯 Notification Types

| Type               | Recipient | Trigger                      | Purpose                              |
| ------------------ | --------- | ---------------------------- | ------------------------------------ |
| `ORDER_CREATED`    | Seller    | Buyer places order           | Alert seller to accept/reject        |
| `ORDER_ACCEPTED`   | Buyer     | Seller accepts order         | Confirm seller is preparing item     |
| `ORDER_DELIVERED`  | Buyer     | Seller marks as delivered    | Prompt buyer to confirm receipt      |
| `ORDER_CONFIRMED`  | Seller    | Buyer confirms receipt       | Notify payment released to wallet    |
| `ORDER_CANCELLED`  | Both      | Order cancelled by either    | Inform about cancellation and refund |
| `PAYMENT_RECEIVED` | Seller    | Payment released from escrow | Confirm wallet credited              |
| `REFUND_ISSUED`    | Buyer     | Refund processed             | Confirm refund to wallet             |

---

## 🚀 Usage Examples

### Example 1: Send Notification When Order Created

```python
from notifications.services import NotificationService

def create_order(buyer, product):
    # ... create order logic ...

    # Send notification to seller
    NotificationService.send_order_created_notification(
        seller=product.store.seller,
        order=order
    )
```

### Example 2: Send Notification When Seller Accepts

```python
def accept_order(order):
    order.status = "ACCEPTED"
    order.save()

    # Notify buyer
    NotificationService.send_order_accepted_notification(
        buyer=order.buyer,
        order=order
    )
```

### Example 3: Send Notification When Buyer Confirms

```python
def confirm_order(order):
    order.status = "CONFIRMED"
    order.save()

    # Release escrow payment...

    # Notify seller about payment
    NotificationService.send_order_confirmed_notification(
        seller=order.seller,
        order=order
    )
```

### Example 4: Send Notification When Order Cancelled

```python
def cancel_order(order, cancelled_by, reason):
    order.status = "CANCELLED"
    order.save()

    # Refund buyer...

    # Notify both parties
    NotificationService.send_order_cancelled_notification(
        user=order.buyer,
        order=order,
        cancelled_by=cancelled_by,
        reason=reason
    )

    NotificationService.send_order_cancelled_notification(
        user=order.seller,
        order=order,
        cancelled_by=cancelled_by,
        reason=reason
    )
```

---

## 📊 Database Model

### Notification Model Fields

```python
class Notification(models.Model):
    # Recipient
    user                - User who receives notification

    # Content
    notification_type   - Type (ORDER_CREATED, ORDER_ACCEPTED, etc.)
    title              - Short title/subject
    message            - Full message content

    # Related Data
    order              - Related order (if applicable)

    # Delivery Status
    is_sent            - Whether successfully sent
    sent_at            - Timestamp of delivery
    delivery_method    - How sent (CONSOLE, WHATSAPP, EMAIL, SMS)
    error_message      - Error if failed

    # Timestamps
    created_at         - When notification created
```

### Database Indexes

- `(user, -created_at)` - Fast lookup of user's notification history
- `notification_type` - Filter by type
- `is_sent` - Find pending/failed notifications

---

## 🔧 Current Implementation (Console Logging)

The current implementation **logs to console** instead of sending to WhatsApp. This is perfect for development and testing.

### Console Output Example

```
============================================================
📱 NOTIFICATION TO: seller@example.com
📞 Phone: +2348012345678
============================================================
TITLE: New Order #ORD-20251019-ABC123
------------------------------------------------------------
🛍️ NEW ORDER RECEIVED!

Order: #ORD-20251019-ABC123
Product: Premium Cotton T-Shirt
Price: ₦5,000.00
Delivery Fee: ₦1,000.00
Total: ₦6,000.00

Buyer: John Doe
Location: Ikeja, Lagos

⚡ Please accept or reject this order in your dashboard.
============================================================
```

---

## 🔌 WhatsApp Integration (When Ready)

### What You Need

1. **WhatsApp Business API Credentials**:

   - API URL (e.g., `https://graph.facebook.com/v17.0/YOUR_PHONE_ID/messages`)
   - Access Token
   - Phone Number ID

2. **Update Settings** (`covu/settings.py`):

```python
# WhatsApp Configuration
WHATSAPP_API_URL = env("WHATSAPP_API_URL")
WHATSAPP_API_TOKEN = env("WHATSAPP_API_TOKEN")
WHATSAPP_PHONE_NUMBER_ID = env("WHATSAPP_PHONE_NUMBER_ID")
```

3. **Update Notification Service** (`notifications/services.py`):

Replace `_send_via_whatsapp()` method with:

```python
@staticmethod
def _send_via_whatsapp(notification):
    """Send notification via WhatsApp Business API."""
    import requests
    from django.conf import settings

    url = f"{settings.WHATSAPP_API_URL}/{settings.WHATSAPP_PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {settings.WHATSAPP_API_TOKEN}",
        "Content-Type": "application/json"
    }

    data = {
        "messaging_product": "whatsapp",
        "to": notification.user.phone_number,
        "type": "text",
        "text": {
            "body": notification.message
        }
    }

    response = requests.post(url, json=data, headers=headers)
    response.raise_for_status()

    notification.delivery_method = "WHATSAPP"
```

4. **Update Notification Flow**:

In `_send_notification()`, change from:

```python
NotificationService._send_via_console(notification)
```

To:

```python
NotificationService._send_via_whatsapp(notification)
```

That's it! All message templates and logic remain the same.

---

## 🎨 Admin Interface

Access the admin panel to view all notifications:

**URL**: `http://127.0.0.1:8000/admin/notifications/notification/`

### Features

- ✅ Color-coded notification types
- ✅ Delivery status badges (Sent/Failed/Pending)
- ✅ Filter by type, status, date
- ✅ Search by user email, title, message
- ✅ View full message content
- ✅ Track delivery method (Console/WhatsApp/Email/SMS)
- ✅ Error messages for failed notifications

### Admin Actions

- ❌ **Cannot manually create** - System creates automatically
- ✅ **Can delete** - For cleanup (unlike orders/escrow)
- ✅ **Can view history** - Complete notification log

---

## 🧪 Testing in Django Shell

```python
# Open Django shell
python manage.py shell

# Import dependencies
from users.models import CustomUser
from orders.models import Order
from notifications.services import NotificationService

# Get test data
seller = CustomUser.objects.get(email='seller@example.com')
buyer = CustomUser.objects.get(email='buyer@example.com')
order = Order.objects.first()

# Test notification
notification = NotificationService.send_order_created_notification(
    seller=seller,
    order=order
)

# Verify notification
print(f"Title: {notification.title}")
print(f"Sent: {notification.is_sent}")
print(f"Method: {notification.delivery_method}")
print(f"Message:\n{notification.message}")

# Check in database
from notifications.models import Notification
Notification.objects.filter(user=seller).count()
```

---

## 📁 File Structure

```
notifications/
├── __init__.py
├── models.py           # Notification model
├── services.py         # NotificationService class (main logic)
├── admin.py            # Admin interface
├── examples.py         # Usage examples and integration guide
├── README.md           # This file
├── apps.py            # App configuration
├── migrations/        # Database migrations
└── tests.py           # Unit tests (to be added)
```

---

## ✅ Integration Checklist

When integrating notifications into your order service layer:

- [ ] Import `NotificationService` in `orders/services.py`
- [ ] Call `send_order_created_notification()` after creating order
- [ ] Call `send_order_accepted_notification()` after seller accepts
- [ ] Call `send_order_delivered_notification()` after seller delivers
- [ ] Call `send_order_confirmed_notification()` after buyer confirms
- [ ] Call `send_order_cancelled_notification()` for both parties when cancelled
- [ ] Test notifications in Django shell
- [ ] Verify notifications appear in admin panel
- [ ] Check console logs for notification output

---

## 🔮 Future Enhancements

When WhatsApp API is integrated, consider adding:

1. **Message Templates** - WhatsApp approved templates
2. **Media Messages** - Send product images with notifications
3. **Quick Reply Buttons** - "Accept Order" / "Reject Order" buttons
4. **Delivery Status** - Track message delivery and read receipts
5. **Retry Logic** - Automatic retry for failed messages
6. **Rate Limiting** - Respect WhatsApp API limits
7. **Fallback to SMS/Email** - If WhatsApp fails
8. **User Preferences** - Let users choose notification method

---

## 📞 Support

For questions about the notifications app:

1. Check `examples.py` for usage examples
2. Review `services.py` for available methods
3. Test in Django shell before integrating
4. Check admin panel for notification history

---

_Last Updated: October 19, 2025_  
_Status: Ready for Phase 3 integration_
