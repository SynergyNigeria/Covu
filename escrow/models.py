from django.db import models
from orders.models import Order
from wallets.models import Wallet
import uuid


# ==============================================================================
# ESCROW TRANSACTION MODEL
# ==============================================================================


class EscrowTransaction(models.Model):
    """
    Escrow system for secure payment holding.

    Flow:
    1. HELD: Money deducted from buyer, held in escrow
    2. RELEASED: Money credited to seller (order confirmed)
    3. REFUNDED: Money returned to buyer (order cancelled)

    One escrow transaction per order.
    Money stays in escrow until buyer confirms delivery.
    """

    STATUS_CHOICES = [
        ("HELD", "Funds Held in Escrow"),
        ("RELEASED", "Funds Released to Seller"),
        ("REFUNDED", "Funds Refunded to Buyer"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Relationships (OneToOne ensures one escrow per order)
    order = models.OneToOneField(
        Order,
        on_delete=models.PROTECT,
        related_name="escrow",
        help_text="Order this escrow is for",
    )
    buyer_wallet = models.ForeignKey(
        Wallet,
        on_delete=models.PROTECT,
        related_name="escrow_debits",
        help_text="Buyer's wallet (money came from here)",
    )
    seller_wallet = models.ForeignKey(
        Wallet,
        on_delete=models.PROTECT,
        related_name="escrow_credits",
        help_text="Seller's wallet (money will go here)",
    )

    # Escrow Details
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Total amount held in escrow (product + delivery)",
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="HELD",
        db_index=True,
        help_text="Current escrow status",
    )

    # Transaction References (for wallet audit trail)
    debit_reference = models.CharField(
        max_length=100,
        unique=True,
        help_text="Reference for buyer's wallet debit transaction",
    )
    credit_reference = models.CharField(
        max_length=100,
        unique=True,
        null=True,
        blank=True,
        help_text="Reference for seller's wallet credit transaction (when released)",
    )
    refund_reference = models.CharField(
        max_length=100,
        unique=True,
        null=True,
        blank=True,
        help_text="Reference for buyer's wallet refund transaction (when refunded)",
    )

    # Timestamps
    held_at = models.DateTimeField(
        auto_now_add=True, help_text="When funds were held in escrow"
    )
    released_at = models.DateTimeField(
        null=True, blank=True, help_text="When funds were released to seller"
    )
    refunded_at = models.DateTimeField(
        null=True, blank=True, help_text="When funds were refunded to buyer"
    )

    # Metadata
    notes = models.TextField(
        blank=True, help_text="Internal notes about this escrow transaction"
    )

    class Meta:
        db_table = "escrow_transactions"
        verbose_name = "Escrow Transaction"
        verbose_name_plural = "Escrow Transactions"
        ordering = ["-held_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["held_at"]),
        ]

    def __str__(self):
        return f"Escrow #{str(self.id)[:8]} - ₦{self.amount} ({self.status})"

    @property
    def is_held(self):
        """Check if funds are currently held."""
        return self.status == "HELD"

    @property
    def is_released(self):
        """Check if funds have been released to seller."""
        return self.status == "RELEASED"

    @property
    def is_refunded(self):
        """Check if funds have been refunded to buyer."""
        return self.status == "REFUNDED"

    @property
    def days_held(self):
        """Calculate how many days funds have been held."""
        from django.utils import timezone

        if self.status == "HELD":
            return (timezone.now() - self.held_at).days
        elif self.released_at:
            return (self.released_at - self.held_at).days
        elif self.refunded_at:
            return (self.refunded_at - self.held_at).days
        return 0
