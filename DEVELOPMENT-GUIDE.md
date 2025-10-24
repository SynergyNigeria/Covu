# COVU Development Guide

**Complete implementation reference for developers**

---

## Table of Contents

1. [Project Architecture](#project-architecture)
2. [Wallet System Implementation](#wallet-system-implementation)
3. [Paystack Integration](#paystack-integration)
4. [Escrow System Guide](#escrow-system-guide)
5. [Email Notifications](#email-notifications)
6. [Store Listing Algorithm](#store-listing-algorithm)
7. [Security Best Practices](#security-best-practices)
8. [Code Examples](#code-examples)

---

## 1. Project Architecture

### Design Principles

**1. Wallet-First Approach**

- All users get auto-created wallets on registration
- Internal transactions NEVER touch Paystack
- Paystack ONLY for funding & withdrawals
- Complete audit trail for every naira moved

**2. Escrow Protection**

- Money deducted from buyer → Held in escrow → Released to seller
- Protects both parties from fraud
- 7-day confirmation window
- Auto-release if no disputes

**3. Atomic Transactions**

- All wallet operations use `transaction.atomic()`
- Either ALL steps succeed or ALL fail
- No partial transactions
- No money lost or duplicated

### Database Models Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    COVU DATA MODEL                           │
└─────────────────────────────────────────────────────────────┘

CustomUser
├── id (auto)
├── email (unique)
├── phone_number (unique)
├── full_name
├── state (Nigerian states)
├── city (LGA)
└── wallet (OneToOne) ─────┐
                           │
                           ▼
                    Wallet
                    ├── id (UUID)
                    ├── user (OneToOne)
                    ├── balance (computed)
                    ├── currency (NGN)
                    └── transactions (reverse FK) ─────┐
                                                       │
                                                       ▼
                                            WalletTransaction
                                            ├── id (UUID)
                                            ├── wallet (FK)
                                            ├── type (CREDIT/DEBIT/ESCROW_*)
                                            ├── amount
                                            ├── balance_before
                                            ├── balance_after
                                            └── reference (unique)

Store                               Order
├── id (UUID)                       ├── id (UUID)
├── owner (FK → User)               ├── buyer (FK → User)
├── name                            ├── store (FK → Store)
├── description                     ├── total_amount
├── location (state, city)          ├── status
└── products (reverse FK)           └── escrow (OneToOne) ──┐
                                                             │
                                                             ▼
Product                                          EscrowTransaction
├── id (UUID)                                    ├── id (UUID)
├── store (FK)                                   ├── order (OneToOne)
├── name                                         ├── buyer_wallet (FK)
├── price                                        ├── seller_wallet (FK)
├── category                                     ├── amount
├── image (Cloudinary)                           ├── status (HELD/RELEASED/REFUNDED)
└── key_features (JSON)                          └── timestamps
```

---

## 2. Wallet System Implementation

### Wallet Auto-Creation (Django Signal)

```python
# users/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from wallets.models import Wallet

@receiver(post_save, sender=CustomUser)
def create_wallet(sender, instance, created, **kwargs):
    """Auto-create wallet for new users"""
    if created:
        Wallet.objects.create(user=instance)
        logger.info(f"Wallet created for user: {instance.email}")
```

### Wallet Transaction Pattern

**ALWAYS use this pattern for ANY wallet operation:**

```python
from django.db import transaction
from decimal import Decimal

def perform_wallet_operation(wallet, amount, transaction_type, description):
    """
    Safe wallet operation with atomic transaction

    Args:
        wallet: Wallet instance
        amount: Decimal (positive for credit, negative for debit)
        transaction_type: 'CREDIT', 'DEBIT', 'ESCROW_HOLD', etc.
        description: Human-readable description
    """
    with transaction.atomic():
        # Lock wallet to prevent race conditions
        wallet = Wallet.objects.select_for_update().get(id=wallet.id)

        # Get current balance
        balance_before = wallet.balance

        # Calculate new balance
        balance_after = balance_before + amount

        # Validate (prevent negative balance for debits)
        if balance_after < 0:
            raise ValueError("Insufficient balance")

        # Create transaction record
        WalletTransaction.objects.create(
            wallet=wallet,
            transaction_type=transaction_type,
            amount=amount,
            balance_before=balance_before,
            balance_after=balance_after,
            reference=generate_unique_reference(),
            description=description
        )

        # Balance is auto-computed from transactions
        # No need to manually update wallet.balance

    return wallet
```

### Wallet Balance Calculation

The wallet balance is **NEVER stored** directly. It's **COMPUTED** from all transactions:

```python
# wallets/models.py
class Wallet(models.Model):
    # ... fields ...

    @property
    def balance(self):
        """Calculate balance from all transactions"""
        from django.db.models import Sum

        total = self.transactions.aggregate(
            Sum('amount')
        )['amount__sum'] or Decimal('0.00')

        return total
```

**Why computed balance?**

- ✅ Single source of truth (transactions)
- ✅ Cannot be manipulated directly
- ✅ Audit trail is the balance
- ✅ Easy to detect inconsistencies

---

## 3. Paystack Integration

### Payment Initialization

```python
# wallets/views.py
class FundWalletView(generics.CreateAPIView):
    def create(self, request):
        amount = request.data['amount']
        user = request.user

        # Convert to kobo (Paystack uses kobo)
        amount_in_kobo = int(amount * 100)

        # Generate unique reference
        reference = f"WALLET_FUND_{user.id}_{uuid.uuid4().hex[:12].upper()}"

        # Initialize Paystack payment
        response = requests.post(
            "https://api.paystack.co/transaction/initialize",
            headers={
                "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "email": user.email,
                "amount": amount_in_kobo,
                "reference": reference,
                "callback_url": f"{FRONTEND_URL}/wallet/verify",
                "metadata": {
                    "user_id": str(user.id),
                    "wallet_id": str(user.wallet.id),
                    "purpose": "wallet_funding"
                }
            }
        )

        data = response.json()

        return Response({
            "authorization_url": data["data"]["authorization_url"],
            "reference": reference,
            "amount": float(amount)
        })
```

### Webhook Handler

```python
class PaystackWebhookView(APIView):
    permission_classes = []  # No auth needed

    def post(self, request):
        # 1. Verify signature
        signature = request.headers.get("X-Paystack-Signature")
        payload = request.body

        expected_signature = hmac.new(
            PAYSTACK_SECRET_KEY.encode('utf-8'),
            payload,
            hashlib.sha512
        ).hexdigest()

        if signature != expected_signature:
            return Response({"status": "error"}, status=401)

        # 2. Parse data
        data = request.data
        event = data.get("event")

        if event == "charge.success":
            payment_data = data.get("data", {})
            reference = payment_data.get("reference")
            amount_in_kobo = payment_data.get("amount")
            metadata = payment_data.get("metadata", {})

            user_id = metadata.get("user_id")
            wallet_id = metadata.get("wallet_id")
            amount = amount_in_kobo / 100  # Convert to naira

            # 3. Credit wallet atomically
            with transaction.atomic():
                wallet = Wallet.objects.select_for_update().get(id=wallet_id)

                # Check idempotency (prevent duplicate processing)
                if WalletTransaction.objects.filter(reference=reference).exists():
                    return Response({"status": "success"})

                balance_before = wallet.balance

                # Create CREDIT transaction
                WalletTransaction.objects.create(
                    wallet=wallet,
                    transaction_type="CREDIT",
                    amount=amount,
                    balance_before=balance_before,
                    balance_after=balance_before + amount,
                    reference=reference,
                    description=f"Wallet funding via Paystack - {reference}"
                )

                # Send email notification
                EmailNotificationService.send_wallet_funded(
                    user=wallet.user,
                    amount=amount,
                    reference=reference
                )

            return Response({"status": "success"})

        return Response({"status": "success"})
```

### Withdrawal with Tiered Fees

```python
class WithdrawFundsView(generics.CreateAPIView):
    def create(self, request):
        amount = Decimal(request.data['amount'])
        bank_account_id = request.data['bank_account_id']
        user = request.user

        # Calculate tiered fee
        if amount < Decimal("10000.00"):
            fee = Decimal("100.00")      # ₦2K-₦9,999
        elif amount < Decimal("50000.00"):
            fee = Decimal("150.00")      # ₦10K-₦49,999
        elif amount < Decimal("100000.00"):
            fee = Decimal("200.00")      # ₦50K-₦99,999
        elif amount <= Decimal("200000.00"):
            fee = Decimal("250.00")      # ₦100K-₦200K
        else:
            fee = Decimal("300.00")      # ₦200K+

        total_debit = amount + fee

        # Validate balance
        if user.wallet.balance < total_debit:
            return Response({
                "error": f"Insufficient balance. Need ₦{total_debit:,.2f}"
            }, status=400)

        # Get bank account
        bank_account = BankAccount.objects.get(id=bank_account_id, user=user)

        with transaction.atomic():
            # Debit wallet
            wallet = Wallet.objects.select_for_update().get(user=user)
            balance_before = wallet.balance

            WalletTransaction.objects.create(
                wallet=wallet,
                transaction_type="DEBIT",
                amount=-total_debit,
                balance_before=balance_before,
                balance_after=balance_before - total_debit,
                reference=f"WITHDRAW_{user.id}_{uuid.uuid4().hex[:12]}",
                description=f"Withdrawal to {bank_account.bank_name}"
            )

            # Create withdrawal record
            withdrawal = Withdrawal.objects.create(
                user=user,
                wallet=wallet,
                bank_account=bank_account,
                amount=amount,
                fee=fee,
                net_amount=amount,
                status="PENDING"
            )

            # Call Paystack Transfer API
            response = requests.post(
                "https://api.paystack.co/transfer",
                headers={"Authorization": f"Bearer {PAYSTACK_SECRET_KEY}"},
                json={
                    "source": "balance",
                    "amount": int(amount * 100),  # Kobo
                    "recipient": bank_account.paystack_recipient_code,
                    "reason": f"Withdrawal - {withdrawal.id}",
                    "reference": str(withdrawal.id)
                }
            )

            if response.status_code == 200:
                withdrawal.status = "PROCESSING"
                withdrawal.save()

                # Send email
                EmailNotificationService.send_withdrawal_initiated(
                    user=user,
                    amount=amount,
                    fee=fee,
                    bank_name=bank_account.bank_name
                )

        return Response({
            "status": "success",
            "data": {
                "amount": float(amount),
                "fee": float(fee),
                "net_amount": float(amount),
                "new_balance": float(wallet.balance)
            }
        })
```

---

## 4. Escrow System Guide

### Complete Escrow Flow

```python
# orders/services.py
from decimal import Decimal
from django.db import transaction
import uuid

def create_order_with_escrow(buyer, store, cart_items, delivery_address):
    """
    Create order and hold funds in escrow

    Flow:
    1. Calculate total (products + delivery)
    2. Validate buyer has sufficient funds
    3. Create order
    4. Deduct from buyer's wallet (ESCROW_HOLD)
    5. Create escrow transaction (status=HELD)
    6. Notify seller via WhatsApp

    Returns: Order instance
    """

    # Calculate totals
    product_total = sum(
        item['product'].price * item['quantity']
        for item in cart_items
    )
    delivery_fee = Decimal("500.00")  # Or calculate based on location
    total_amount = product_total + delivery_fee

    # Validate balance
    if buyer.wallet.balance < total_amount:
        raise InsufficientFundsError(
            f"Need ₦{total_amount:,.2f}, have ₦{buyer.wallet.balance:,.2f}"
        )

    # Use atomic transaction (all or nothing)
    with transaction.atomic():
        # 1. Create order
        order = Order.objects.create(
            buyer=buyer,
            store=store,
            total_amount=total_amount,
            delivery_address=delivery_address,
            status="PENDING"
        )

        # 2. Create order items
        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=item['product'],
                quantity=item['quantity'],
                price=item['product'].price
            )

        # 3. Deduct from buyer's wallet (ESCROW_HOLD)
        buyer_wallet = Wallet.objects.select_for_update().get(user=buyer)
        balance_before = buyer_wallet.balance

        debit_reference = f"ESCROW_HOLD_{order.id}"

        WalletTransaction.objects.create(
            wallet=buyer_wallet,
            transaction_type="ESCROW_HOLD",
            amount=-total_amount,
            balance_before=balance_before,
            balance_after=balance_before - total_amount,
            reference=debit_reference,
            description=f"Order #{order.id} - Funds held in escrow"
        )

        # 4. Create escrow record
        EscrowTransaction.objects.create(
            order=order,
            buyer_wallet=buyer_wallet,
            seller_wallet=store.owner.wallet,
            amount=total_amount,
            status="HELD",
            debit_reference=debit_reference
        )

    # 5. Send WhatsApp notification to seller
    send_whatsapp_notification(
        phone=store.owner.phone_number,
        message=f"🛍️ New Order!\n\nOrder #{order.id}\nBuyer: {buyer.full_name}\nTotal: ₦{total_amount:,.2f}\n\nReview order in app."
    )

    # 6. Send email to buyer
    EmailNotificationService.send_order_created(
        user=buyer,
        order=order
    )

    return order
```

### Confirm Delivery (Release Escrow)

```python
def confirm_delivery(order):
    """
    Buyer confirms delivery - release funds to seller

    Flow:
    1. Validate order can be confirmed
    2. Get escrow transaction
    3. Credit seller's wallet (ESCROW_RELEASE)
    4. Update escrow status to RELEASED
    5. Update order status to COMPLETED
    6. Notify both parties
    """

    # Validate
    if order.status != "DELIVERED":
        raise ValidationError("Order must be delivered first")

    if order.escrow.status != "HELD":
        raise ValidationError("Escrow already processed")

    with transaction.atomic():
        escrow = order.escrow

        # Credit seller's wallet
        seller_wallet = Wallet.objects.select_for_update().get(
            id=escrow.seller_wallet.id
        )
        balance_before = seller_wallet.balance

        credit_reference = f"ESCROW_RELEASE_{order.id}"

        WalletTransaction.objects.create(
            wallet=seller_wallet,
            transaction_type="ESCROW_RELEASE",
            amount=escrow.amount,
            balance_before=balance_before,
            balance_after=balance_before + escrow.amount,
            reference=credit_reference,
            description=f"Order #{order.id} - Payment released"
        )

        # Update escrow
        escrow.status = "RELEASED"
        escrow.credit_reference = credit_reference
        escrow.released_at = timezone.now()
        escrow.save()

        # Update order
        order.status = "COMPLETED"
        order.save()

    # Notifications
    EmailNotificationService.send_order_completed(
        user=order.buyer,
        order=order
    )
    EmailNotificationService.send_payment_received(
        user=order.store.owner,
        order=order,
        amount=escrow.amount
    )

    return order
```

### Refund Order (Dispute)

```python
def refund_order(order, reason):
    """
    Refund order - return funds to buyer

    Flow:
    1. Validate order can be refunded
    2. Get escrow transaction
    3. Credit buyer's wallet (ESCROW_REFUND)
    4. Update escrow status to REFUNDED
    5. Update order status to REFUNDED
    6. Notify both parties
    """

    # Validate
    if order.escrow.status != "HELD":
        raise ValidationError("Escrow already processed")

    with transaction.atomic():
        escrow = order.escrow

        # Refund to buyer
        buyer_wallet = Wallet.objects.select_for_update().get(
            id=escrow.buyer_wallet.id
        )
        balance_before = buyer_wallet.balance

        refund_reference = f"ESCROW_REFUND_{order.id}"

        WalletTransaction.objects.create(
            wallet=buyer_wallet,
            transaction_type="ESCROW_REFUND",
            amount=escrow.amount,
            balance_before=balance_before,
            balance_after=balance_before + escrow.amount,
            reference=refund_reference,
            description=f"Order #{order.id} - Refund: {reason}"
        )

        # Update escrow
        escrow.status = "REFUNDED"
        escrow.refund_reference = refund_reference
        escrow.refunded_at = timezone.now()
        escrow.notes = reason
        escrow.save()

        # Update order
        order.status = "REFUNDED"
        order.save()

    # Notifications
    EmailNotificationService.send_order_refunded(
        user=order.buyer,
        order=order,
        reason=reason
    )
    EmailNotificationService.send_order_cancelled(
        user=order.store.owner,
        order=order,
        reason=reason
    )

    return order
```

### Auto-Release (Celery Task)

```python
# escrow/tasks.py
from celery import shared_task
from django.utils import timezone
from datetime import timedelta

@shared_task
def auto_release_old_escrows():
    """
    Run daily: Auto-release escrows for orders delivered 7+ days ago

    Business Rules:
    - Order must be DELIVERED
    - Delivered at least 7 days ago
    - Escrow still HELD (not manually confirmed/refunded)

    Action: Automatically confirm delivery → release to seller
    """

    seven_days_ago = timezone.now() - timedelta(days=7)

    # Find eligible orders
    old_orders = Order.objects.filter(
        status="DELIVERED",
        delivered_at__lte=seven_days_ago,
        escrow__status="HELD"
    ).select_related('escrow', 'buyer', 'store__owner')

    for order in old_orders:
        try:
            # Auto-confirm delivery
            confirm_delivery(order)

            logger.info(f"Auto-released escrow for order {order.id}")

            # Send special notification about auto-release
            EmailNotificationService.send_order_auto_confirmed(
                user=order.buyer,
                order=order
            )
            EmailNotificationService.send_payment_auto_released(
                user=order.store.owner,
                order=order
            )

        except Exception as e:
            logger.error(f"Failed to auto-release order {order.id}: {e}")
            # Don't stop - continue with other orders

    return f"Processed {old_orders.count()} orders"

# celery.py (setup)
from celery.schedules import crontab

app.conf.beat_schedule = {
    'auto-release-escrows-daily': {
        'task': 'escrow.tasks.auto_release_old_escrows',
        'schedule': crontab(hour=2, minute=0),  # Run at 2 AM daily
    },
}
```

---

## 5. Email Notifications

### Available Notification Types (10 Total)

```python
# notifications/email_service.py

class EmailNotificationService:

    # WALLET NOTIFICATIONS
    @staticmethod
    def send_wallet_funded(user, amount, reference):
        """Wallet successfully funded via Paystack"""
        pass

    @staticmethod
    def send_withdrawal_initiated(user, amount, fee, bank_name):
        """Withdrawal request received"""
        pass

    @staticmethod
    def send_withdrawal_completed(user, amount, bank_name):
        """Withdrawal successfully sent to bank"""
        pass

    @staticmethod
    def send_withdrawal_failed(user, amount, reason):
        """Withdrawal failed - funds refunded"""
        pass

    # ORDER NOTIFICATIONS
    @staticmethod
    def send_order_created(user, order):
        """Order created - funds held in escrow"""
        pass

    @staticmethod
    def send_order_shipped(user, order):
        """Seller shipped your order"""
        pass

    @staticmethod
    def send_order_delivered(user, order):
        """Order marked as delivered - confirm receipt"""
        pass

    @staticmethod
    def send_order_completed(user, order):
        """Order confirmed - funds released to seller"""
        pass

    @staticmethod
    def send_order_refunded(user, order, reason):
        """Order refunded - money returned to wallet"""
        pass

    # SELLER NOTIFICATIONS
    @staticmethod
    def send_payment_received(user, order, amount):
        """Seller: Payment received for order"""
        pass
```

### Email Template Example

```html
<!-- notifications/templates/emails/wallet_funded.html -->
<!DOCTYPE html>
<html>
  <head>
    <style>
      body {
        font-family: Arial, sans-serif;
      }
      .container {
        max-width: 600px;
        margin: 0 auto;
        padding: 20px;
      }
      .header {
        background: #4caf50;
        color: white;
        padding: 20px;
        text-align: center;
      }
      .content {
        background: #f9f9f9;
        padding: 30px;
      }
      .amount {
        font-size: 32px;
        font-weight: bold;
        color: #4caf50;
      }
      .footer {
        text-align: center;
        padding: 20px;
        color: #666;
      }
    </style>
  </head>
  <body>
    <div class="container">
      <div class="header">
        <h1>✅ Wallet Funded Successfully!</h1>
      </div>
      <div class="content">
        <p>Hello {{ user.full_name }},</p>
        <p>Your COVU wallet has been successfully funded!</p>

        <div style="text-align: center; margin: 30px 0;">
          <div class="amount">₦{{ amount|floatformat:2|intcomma }}</div>
          <p>Added to your wallet</p>
        </div>

        <p><strong>Transaction Details:</strong></p>
        <ul>
          <li>Reference: {{ reference }}</li>
          <li>Date: {{ now|date:"F d, Y - h:i A" }}</li>
          <li>
            New Balance: ₦{{ user.wallet.balance|floatformat:2|intcomma }}
          </li>
        </ul>

        <p>You can now use this balance to make purchases on COVU!</p>
      </div>
      <div class="footer">
        <p>Thank you for using COVU!</p>
        <p>Questions? Contact support@covu.com</p>
      </div>
    </div>
  </body>
</html>
```

---

## 6. Store Listing Algorithm

### Implementation

```python
# stores/views.py
from django.db.models import Q, F, Count, Avg, Case, When, Value, FloatField
from django.db.models.functions import Random
import random

class StoreListView(generics.ListAPIView):
    def get_queryset(self):
        user = self.request.user

        # Get user's location
        user_state = user.state if user.is_authenticated else None
        user_city = user.city if user.is_authenticated else None

        # Base queryset with annotations
        queryset = Store.objects.annotate(
            # Location scoring (40% total)
            state_match=Case(
                When(state=user_state, then=Value(1.0)),
                default=Value(0.0),
                output_field=FloatField()
            ),
            city_match=Case(
                When(city=user_city, then=Value(1.0)),
                default=Value(0.0),
                output_field=FloatField()
            ),
            location_score=F('state_match') * 0.20 + F('city_match') * 0.20,

            # Quality metrics (60% total)
            avg_rating=Avg('ratings__rating'),
            product_count=Count('products'),
            sales_count=Count('orders'),
            review_count=Count('ratings'),

            # Days since creation (newer = higher score)
            days_old=ExpressionWrapper(
                timezone.now() - F('created_at'),
                output_field=DurationField()
            )
        ).annotate(
            # Normalize scores (0-1 scale)
            rating_score=(F('avg_rating') / 5.0) * 0.15,
            product_score=Case(
                When(product_count__gte=20, then=Value(1.0)),
                When(product_count__gte=10, then=Value(0.7)),
                When(product_count__gte=5, then=Value(0.4)),
                default=Value(0.2),
                output_field=FloatField()
            ) * 0.15,
            sales_score=Case(
                When(sales_count__gte=50, then=Value(1.0)),
                When(sales_count__gte=20, then=Value(0.7)),
                When(sales_count__gte=5, then=Value(0.4)),
                default=Value(0.2),
                output_field=FloatField()
            ) * 0.10,
            review_score=Case(
                When(review_count__gte=30, then=Value(1.0)),
                When(review_count__gte=10, then=Value(0.7)),
                When(review_count__gte=3, then=Value(0.4)),
                default=Value(0.2),
                output_field=FloatField()
            ) * 0.05,
            recency_score=Case(
                When(days_old__lte=30, then=Value(1.0)),
                When(days_old__lte=90, then=Value(0.7)),
                When(days_old__lte=180, then=Value(0.4)),
                default=Value(0.1),
                output_field=FloatField()
            ) * 0.10,

            # Random component (5%)
            random_score=Random() * 0.05,

            # Total score
            total_score=(
                F('location_score') +
                F('rating_score') +
                F('product_score') +
                F('sales_score') +
                F('review_score') +
                F('recency_score') +
                F('random_score')
            )
        ).order_by('-total_score')

        return queryset
```

---

## 7. Security Best Practices

### 1. Always Use Atomic Transactions

```python
# ❌ WRONG - Race condition possible
wallet.balance -= amount
wallet.save()

# ✅ CORRECT - Atomic with SELECT FOR UPDATE
with transaction.atomic():
    wallet = Wallet.objects.select_for_update().get(id=wallet.id)
    # Perform operations...
```

### 2. Validate Before Every Operation

```python
# Always check balance before debit
if wallet.balance < amount:
    raise InsufficientFundsError()

# Always verify ownership
if bank_account.user != request.user:
    raise PermissionDenied()
```

### 3. Use Unique References

```python
# Prevent duplicate processing
reference = f"TXN_{user.id}_{uuid.uuid4().hex[:12].upper()}"

if WalletTransaction.objects.filter(reference=reference).exists():
    return  # Already processed
```

### 4. Verify Webhook Signatures

```python
# Always verify Paystack webhooks
expected = hmac.new(
    SECRET_KEY.encode('utf-8'),
    request.body,
    hashlib.sha512
).hexdigest()

if signature != expected:
    return Response(status=401)
```

---

## 8. Code Examples

### Complete Order Creation Flow

```python
# Example: User places order
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_order(request):
    """
    POST /api/orders/
    {
        "store_id": "uuid",
        "items": [
            {"product_id": "uuid", "quantity": 2},
            {"product_id": "uuid", "quantity": 1}
        ],
        "delivery_address": {
            "street": "123 Main St",
            "city": "Ikeja",
            "state": "lagos"
        }
    }
    """

    serializer = OrderSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    # Create order with escrow
    order = create_order_with_escrow(
        buyer=request.user,
        store_id=serializer.validated_data['store_id'],
        cart_items=serializer.validated_data['items'],
        delivery_address=serializer.validated_data['delivery_address']
    )

    return Response({
        "status": "success",
        "message": "Order created. Funds held in escrow.",
        "data": OrderSerializer(order).data
    }, status=201)
```

---

## Next Steps

After completing this guide:

1. Implement Order model
2. Build escrow creation logic
3. Add confirmation/dispute APIs
4. Set up Celery for auto-release
5. Integrate WhatsApp notifications
6. Test complete flow

**Total Estimated Time**: 2-3 weeks

---

_This guide is living documentation. Update as you implement features._
