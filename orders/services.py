"""
Order Service Layer - Business Logic for Order Management

This module contains all business logic for order operations:
- create_order: Create order with wallet debit and escrow hold
- accept_order: Seller accepts order
- deliver_order: Seller marks as delivered
- confirm_order: Buyer confirms, release escrow to seller
- cancel_order: Cancel with refund to buyer

All methods use transaction.atomic() for data consistency.
"""

from django.db import transaction
from django.utils import timezone
from decimal import Decimal
from .models import Order
from escrow.models import EscrowTransaction
from wallets.models import WalletTransaction
from notifications.services import NotificationService
import logging

logger = logging.getLogger("orders")


class InsufficientFundsError(Exception):
    """Raised when wallet balance is insufficient"""

    pass


class InvalidOrderStatusError(Exception):
    """Raised when order status doesn't allow the operation"""

    pass


class PermissionDeniedError(Exception):
    """Raised when user doesn't have permission for the operation"""

    pass


class OrderService:
    """
    Service class for order management operations.
    All methods are atomic to ensure data consistency.
    """

    @staticmethod
    @transaction.atomic
    def create_order(buyer, product, delivery_address):
        """
        Create a new order with wallet debit and escrow hold.

        Process:
        1. Calculate delivery fee based on location
        2. Validate buyer wallet balance
        3. Debit buyer wallet
        4. Create order (status=PENDING)
        5. Create escrow transaction (status=HELD)
        6. Send notification to seller

        Args:
            buyer: CustomUser instance (buyer)
            product: Product instance
            delivery_address: String (delivery address)

        Returns:
            Order instance

        Raises:
            InsufficientFundsError: If buyer wallet balance is insufficient
        """
        store = product.store
        seller = store.seller

        # 1. Calculate delivery fee based on buyer's location vs seller's location
        if buyer.city == seller.city and buyer.state == seller.state:
            delivery_fee = store.delivery_within_lga
            logger.info(f"Same city delivery: {buyer.city}, {buyer.state}")
        else:
            delivery_fee = store.delivery_outside_lga
            logger.info(
                f"Cross-location delivery: Buyer({buyer.city}, {buyer.state}) -> Seller({seller.city}, {seller.state})"
            )

        # Calculate total amount
        total_amount = product.price + delivery_fee

        # 2. Validate buyer wallet balance
        buyer_balance = buyer.wallet.balance
        if buyer_balance < total_amount:
            error_msg = f"Insufficient funds. Need ₦{total_amount:.2f}, have ₦{buyer_balance:.2f}"
            logger.error(error_msg)
            raise InsufficientFundsError(error_msg)

        # 3. Debit buyer wallet (create DEBIT transaction)
        buyer_wallet = buyer.wallet
        balance_before = buyer_wallet.balance
        balance_after = balance_before - total_amount

        # Generate order number using timestamp and buyer ID
        import random
        import string

        random_suffix = "".join(
            random.choices(string.ascii_uppercase + string.digits, k=6)
        )
        order_number = f"ORD-{timezone.now().strftime('%Y%m%d')}-{random_suffix}"

        debit_transaction = WalletTransaction.objects.create(
            wallet=buyer_wallet,
            transaction_type="DEBIT",
            amount=total_amount,
            reference=order_number,
            description=f"Payment for {product.name}",
            balance_before=balance_before,
            balance_after=balance_after,
            metadata={
                "product_id": str(product.id),
                "product_name": product.name,
                "product_price": float(product.price),
                "delivery_fee": float(delivery_fee),
                "total_amount": float(total_amount),
            },
        )

        logger.info(f"Debited ₦{total_amount:.2f} from buyer {buyer.email} wallet")
        logger.info(f"Wallet balance: ₦{balance_before:.2f} → ₦{balance_after:.2f}")

        # 4. Create Order (status=PENDING)
        order = Order.objects.create(
            buyer=buyer,
            seller=seller,
            product=product,
            product_price=product.price,
            delivery_fee=delivery_fee,
            total_amount=total_amount,
            delivery_address=delivery_address,
            status="PENDING",
        )

        logger.info(f"Order created: {order.order_number}")

        # 5. Create EscrowTransaction (status=HELD)
        escrow = EscrowTransaction.objects.create(
            order=order,
            amount=total_amount,
            status="HELD",
            buyer_wallet=buyer.wallet,
            seller_wallet=seller.wallet,
            debit_reference=debit_transaction.reference,
        )

        logger.info(
            f"Escrow created: ₦{total_amount:.2f} held for order {order.order_number}"
        )

        # 6. Send notification to seller
        NotificationService.send_order_created_notification(seller, order)

        return order

    @staticmethod
    @transaction.atomic
    def accept_order(order, seller):
        """
        Seller accepts the order.

        Process:
        1. Validate seller owns this order
        2. Validate order status is PENDING
        3. Update order status to ACCEPTED
        4. Set accepted_at timestamp
        5. Send notification to buyer

        Args:
            order: Order instance
            seller: CustomUser instance (seller)

        Returns:
            Order instance

        Raises:
            PermissionDeniedError: If seller doesn't own this order
            InvalidOrderStatusError: If order is not PENDING
        """
        # 1. Validate seller owns this order
        if order.seller != seller:
            error_msg = f"Permission denied. Seller {seller.email} does not own order {order.order_number}"
            logger.error(error_msg)
            raise PermissionDeniedError(error_msg)

        # 2. Validate order status is PENDING
        if order.status != "PENDING":
            error_msg = f"Cannot accept order {order.order_number}. Current status: {order.status}, expected: PENDING"
            logger.error(error_msg)
            raise InvalidOrderStatusError(error_msg)

        # 3. Update order status to ACCEPTED
        order.status = "ACCEPTED"

        # 4. Set accepted_at timestamp
        order.accepted_at = timezone.now()
        order.save()

        logger.info(f"Order {order.order_number} accepted by seller {seller.email}")

        # 5. Send notification to buyer
        NotificationService.send_order_accepted_notification(order.buyer, order)

        return order

    @staticmethod
    @transaction.atomic
    def deliver_order(order, seller):
        """
        Seller marks order as delivered.

        Process:
        1. Validate seller owns this order
        2. Validate order status is ACCEPTED
        3. Update order status to DELIVERED
        4. Set delivered_at timestamp
        5. Send notification to buyer

        Args:
            order: Order instance
            seller: CustomUser instance (seller)

        Returns:
            Order instance

        Raises:
            PermissionDeniedError: If seller doesn't own this order
            InvalidOrderStatusError: If order is not ACCEPTED
        """
        # 1. Validate seller owns this order
        if order.seller != seller:
            error_msg = f"Permission denied. Seller {seller.email} does not own order {order.order_number}"
            logger.error(error_msg)
            raise PermissionDeniedError(error_msg)

        # 2. Validate order status is ACCEPTED
        if order.status != "ACCEPTED":
            error_msg = f"Cannot deliver order {order.order_number}. Current status: {order.status}, expected: ACCEPTED"
            logger.error(error_msg)
            raise InvalidOrderStatusError(error_msg)

        # 3. Update order status to DELIVERED
        order.status = "DELIVERED"

        # 4. Set delivered_at timestamp
        order.delivered_at = timezone.now()
        order.save()

        logger.info(
            f"Order {order.order_number} marked as delivered by seller {seller.email}"
        )

        # 5. Send notification to buyer
        NotificationService.send_order_delivered_notification(order.buyer, order)

        return order

    @staticmethod
    @transaction.atomic
    def confirm_order(order, buyer):
        """
        Buyer confirms delivery, release escrow to seller.

        Process:
        1. Validate buyer owns this order
        2. Validate order status is DELIVERED
        3. Update order status to CONFIRMED
        4. Set confirmed_at timestamp
        5. Credit seller wallet
        6. Update escrow status to RELEASED
        7. Send notification to seller

        Args:
            order: Order instance
            buyer: CustomUser instance (buyer)

        Returns:
            Order instance

        Raises:
            PermissionDeniedError: If buyer doesn't own this order
            InvalidOrderStatusError: If order is not DELIVERED
        """
        # 1. Validate buyer owns this order
        if order.buyer != buyer:
            error_msg = f"Permission denied. Buyer {buyer.email} does not own order {order.order_number}"
            logger.error(error_msg)
            raise PermissionDeniedError(error_msg)

        # 2. Validate order status is DELIVERED
        if order.status != "DELIVERED":
            error_msg = f"Cannot confirm order {order.order_number}. Current status: {order.status}, expected: DELIVERED"
            logger.error(error_msg)
            raise InvalidOrderStatusError(error_msg)

        # 3. Update order status to CONFIRMED
        order.status = "CONFIRMED"

        # 4. Set confirmed_at timestamp
        order.confirmed_at = timezone.now()
        order.save()

        logger.info(f"Order {order.order_number} confirmed by buyer {buyer.email}")

        # 5. Credit seller wallet (release escrow funds)
        seller = order.seller
        seller_wallet = seller.wallet
        balance_before = seller_wallet.balance
        balance_after = balance_before + order.total_amount

        credit_transaction = WalletTransaction.objects.create(
            wallet=seller_wallet,
            transaction_type="ESCROW_RELEASE",
            amount=order.total_amount,
            reference=f"ESCROW_RELEASE_{order.order_number}",
            description=f"Payment received for {order.product.name}",
            balance_before=balance_before,
            balance_after=balance_after,
            metadata={
                "order_id": str(order.id),
                "order_number": order.order_number,
                "product_name": order.product.name,
                "buyer_email": buyer.email,
            },
        )

        logger.info(
            f"Credited ₦{order.total_amount:.2f} to seller {seller.email} wallet"
        )
        logger.info(f"Wallet balance: ₦{balance_before:.2f} → ₦{balance_after:.2f}")

        # 6. Update escrow status to RELEASED
        escrow = order.escrow
        escrow.status = "RELEASED"
        escrow.released_at = timezone.now()
        escrow.credit_reference = credit_transaction.reference
        escrow.save()

        logger.info(f"Escrow released for order {order.order_number}")

        # 7. Send notification to seller
        NotificationService.send_order_confirmed_notification(seller, order)

        return order

    @staticmethod
    @transaction.atomic
    def cancel_order(order, cancelled_by, reason):
        """
        Cancel order with refund to buyer.

        Cancellation Rules:
        - Buyer can cancel only while PENDING
        - Seller can cancel anytime before CONFIRMED

        Process:
        1. Validate cancellation rules
        2. Update order status to CANCELLED
        3. Set cancelled_at, cancelled_by, cancellation_reason
        4. Refund buyer wallet
        5. Update escrow status to REFUNDED
        6. Send notifications to both parties

        Args:
            order: Order instance
            cancelled_by: String ('BUYER' or 'SELLER')
            reason: String (cancellation reason)

        Returns:
            Order instance

        Raises:
            InvalidOrderStatusError: If cancellation not allowed
        """
        # 1. Validate cancellation rules
        if cancelled_by == "BUYER":
            # Buyer can cancel only while PENDING
            if order.status != "PENDING":
                error_msg = f"Buyer cannot cancel order {order.order_number}. Current status: {order.status}. Buyer can only cancel while PENDING."
                logger.error(error_msg)
                raise InvalidOrderStatusError(error_msg)

        elif cancelled_by == "SELLER":
            # Seller can cancel anytime before CONFIRMED
            if order.status == "CONFIRMED":
                error_msg = f"Seller cannot cancel order {order.order_number}. Order already CONFIRMED."
                logger.error(error_msg)
                raise InvalidOrderStatusError(error_msg)

        else:
            error_msg = f"Invalid cancelled_by value: {cancelled_by}. Must be 'BUYER' or 'SELLER'."
            logger.error(error_msg)
            raise ValueError(error_msg)

        # 2. Update order status to CANCELLED
        order.status = "CANCELLED"

        # 3. Set cancelled_at, cancelled_by, cancellation_reason
        order.cancelled_at = timezone.now()
        order.cancelled_by = cancelled_by
        order.cancellation_reason = reason
        order.save()

        logger.info(
            f"Order {order.order_number} cancelled by {cancelled_by}. Reason: {reason}"
        )

        # 4. Refund buyer wallet
        buyer = order.buyer
        buyer_wallet = buyer.wallet
        balance_before = buyer_wallet.balance
        refund_amount = order.total_amount
        balance_after = balance_before + refund_amount

        refund_transaction = WalletTransaction.objects.create(
            wallet=buyer_wallet,
            transaction_type="REFUND",
            amount=refund_amount,
            reference=f"REFUND_{order.order_number}",
            description=f"Refund for cancelled order: {order.product.name}",
            balance_before=balance_before,
            balance_after=balance_after,
            metadata={
                "order_id": str(order.id),
                "order_number": order.order_number,
                "cancelled_by": cancelled_by,
                "cancellation_reason": reason,
            },
        )

        logger.info(f"Refunded ₦{order.total_amount:.2f} to buyer {buyer.email} wallet")
        logger.info(f"Wallet balance: ₦{balance_before:.2f} → ₦{balance_after:.2f}")

        # 5. Update escrow status to REFUNDED
        escrow = order.escrow
        escrow.status = "REFUNDED"
        escrow.refunded_at = timezone.now()
        escrow.refund_reference = refund_transaction.reference
        escrow.save()

        logger.info(f"Escrow refunded for order {order.order_number}")

        # 6. Send notifications to both parties
        NotificationService.send_order_cancelled_notification(
            buyer, order, cancelled_by, reason
        )
        NotificationService.send_order_cancelled_notification(
            order.seller, order, cancelled_by, reason
        )

        return order
