from django.db import models
from django.conf import settings
from decimal import Decimal
import uuid
import logging

logger = logging.getLogger("wallets")


# ==============================================================================
# WALLET MODEL
# ==============================================================================


class Wallet(models.Model):
    """
    User wallet for COVU marketplace.

    Key Features:
    - Auto-created on user registration via Django signal
    - Balance is computed from transactions (read-only, cannot be directly manipulated)
    - All operations logged in WalletTransaction for complete audit trail
    - Secured with atomic transactions (no race conditions)
    - Initial balance: ₦0.00

    Security Philosophy:
    - Payment only touches external gateway (Paystack) during fund/withdraw
    - Internal purchases use wallet balance (escrow model)
    - Reduced attack surface for hackers
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="wallet",
        help_text="One wallet per user",
    )
    currency = models.CharField(max_length=3, default="NGN", editable=False)
    is_active = models.BooleanField(
        default=True, help_text="Can be frozen if suspicious activity detected"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "wallets"
        verbose_name = "Wallet"
        verbose_name_plural = "Wallets"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self):
        return f"{self.user.email}'s Wallet (₦{self.balance})"

    @property
    def balance(self):
        """
        Computed balance from transactions (read-only).
        Cannot be directly manipulated - security by design.
        """
        from django.db.models import Sum, Q

        # Credits: Money coming in (funding, escrow release, refunds)
        credits = self.transactions.filter(
            transaction_type__in=["CREDIT", "ESCROW_RELEASE", "REFUND"]
        ).aggregate(Sum("amount"))["amount__sum"] or Decimal("0.00")

        # Debits: Money going out (purchases, escrow hold, withdrawals)
        debits = self.transactions.filter(
            transaction_type__in=["DEBIT", "ESCROW_HOLD", "WITHDRAWAL"]
        ).aggregate(Sum("amount"))["amount__sum"] or Decimal("0.00")

        return credits - debits

    def can_debit(self, amount):
        """Check if wallet has sufficient balance for debit."""
        return self.balance >= amount and self.is_active

    def get_transaction_history(self, limit=10):
        """Get recent transactions."""
        return self.transactions.order_by("-created_at")[:limit]


# ==============================================================================
# WALLET TRANSACTION MODEL
# ==============================================================================


class WalletTransaction(models.Model):
    """
    Complete audit trail of all wallet operations.

    Purpose:
    - Transparency: Every wallet movement is logged
    - Security: Balance computed from transactions (tamper-proof)
    - Compliance: Complete financial audit trail
    - Debugging: Track all wallet operations

    Transaction Types:
    - CREDIT: Paystack funding successful
    - DEBIT: Withdrawal to bank account
    - ESCROW_HOLD: Funds held for purchase (buyer's wallet)
    - ESCROW_RELEASE: Funds released after delivery (seller's wallet)
    - REFUND: Order cancelled/refunded (buyer's wallet)
    """

    TRANSACTION_TYPES = [
        ("CREDIT", "Credit"),  # Paystack funding
        ("DEBIT", "Debit"),  # Purchases
        ("ESCROW_HOLD", "Escrow Hold"),  # Funds held in escrow
        ("ESCROW_RELEASE", "Escrow Release"),  # Funds released to seller
        ("REFUND", "Refund"),  # Order cancelled/refunded
        ("WITHDRAWAL", "Withdrawal"),  # Seller withdraws to bank
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    wallet = models.ForeignKey(
        Wallet, on_delete=models.CASCADE, related_name="transactions"
    )
    transaction_type = models.CharField(
        max_length=20, choices=TRANSACTION_TYPES, db_index=True
    )
    amount = models.DecimalField(
        max_digits=12, decimal_places=2, help_text="Transaction amount in Naira"
    )
    reference = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        help_text="Unique reference for idempotency (prevents duplicate transactions)",
    )
    description = models.TextField(help_text="Transaction description")
    balance_before = models.DecimalField(
        max_digits=12, decimal_places=2, help_text="Wallet balance before transaction"
    )
    balance_after = models.DecimalField(
        max_digits=12, decimal_places=2, help_text="Wallet balance after transaction"
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional transaction data (order_id, paystack_ref, etc.)",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "wallet_transactions"
        verbose_name = "Wallet Transaction"
        verbose_name_plural = "Wallet Transactions"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["wallet", "-created_at"]),
            models.Index(fields=["transaction_type"]),
            models.Index(fields=["reference"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.transaction_type} - ₦{self.amount} ({self.wallet.user.email})"

    def save(self, *args, **kwargs):
        """Log transaction creation."""
        super().save(*args, **kwargs)
        logger.info(
            f"Wallet Transaction: {self.transaction_type} - "
            f"₦{self.amount} for {self.wallet.user.email} "
            f"(Ref: {self.reference})"
        )


# ==============================================================================
# BANK ACCOUNT MODEL (Phase 4 - Withdrawals)
# ==============================================================================


class BankAccount(models.Model):
    """
    User's bank account for withdrawals.

    Features:
    - Store bank details securely
    - One default account per user
    - Paystack recipient code tracking
    - Account verification status
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="bank_accounts"
    )
    bank_name = models.CharField(max_length=100, help_text="Name of the bank")
    bank_code = models.CharField(
        max_length=10, help_text="Paystack bank code (e.g., 058 for GTBank)"
    )
    account_number = models.CharField(
        max_length=10, help_text="10-digit account number"
    )
    account_name = models.CharField(
        max_length=200, help_text="Account holder name (from bank verification)"
    )

    paystack_recipient_code = models.CharField(
        max_length=100, blank=True, help_text="Paystack transfer recipient code"
    )
    is_verified = models.BooleanField(
        default=False, help_text="Bank account verified with Paystack"
    )
    is_default = models.BooleanField(
        default=False, help_text="Default withdrawal account"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "bank_accounts"
        verbose_name = "Bank Account"
        verbose_name_plural = "Bank Accounts"
        ordering = ["-is_default", "-created_at"]
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["is_default"]),
        ]
        # Allow same account number across different banks (e.g., OPay, Moniepoint using phone numbers)
        unique_together = ["user", "account_number", "bank_code"]

    def __str__(self):
        return f"{self.account_name} - {self.bank_name} ({self.account_number})"

    def save(self, *args, **kwargs):
        """Ensure only one default account per user"""
        if self.is_default:
            # Set all other accounts to non-default
            BankAccount.objects.filter(user=self.user, is_default=True).update(
                is_default=False
            )
        super().save(*args, **kwargs)


# ==============================================================================
# WITHDRAWAL MODEL (Phase 4 - Withdrawals)
# ==============================================================================


class Withdrawal(models.Model):
    """
    Withdrawal request tracking.

    Features:
    - Complete audit trail
    - Status tracking (pending, processing, success, failed)
    - Paystack transfer reference
    - Fee tracking
    """

    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("PROCESSING", "Processing"),
        ("SUCCESS", "Success"),
        ("FAILED", "Failed"),
        ("CANCELLED", "Cancelled"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="withdrawals"
    )
    wallet = models.ForeignKey(
        Wallet, on_delete=models.CASCADE, related_name="withdrawals"
    )
    bank_account = models.ForeignKey(
        BankAccount, on_delete=models.SET_NULL, null=True, related_name="withdrawals"
    )

    amount = models.DecimalField(
        max_digits=12, decimal_places=2, help_text="Withdrawal amount (before fees)"
    )
    fee = models.DecimalField(
        max_digits=12, decimal_places=2, default=0, help_text="Paystack transfer fee"
    )
    net_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Amount after fees (credited to bank)",
    )

    reference = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        help_text="Unique withdrawal reference",
    )
    paystack_transfer_code = models.CharField(
        max_length=100, blank=True, help_text="Paystack transfer code"
    )
    paystack_transfer_id = models.BigIntegerField(
        null=True, blank=True, help_text="Paystack transfer ID"
    )

    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="PENDING", db_index=True
    )
    failure_reason = models.TextField(
        blank=True, help_text="Reason for failure (if failed)"
    )

    wallet_transaction = models.ForeignKey(
        WalletTransaction,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="withdrawal",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "withdrawals"
        verbose_name = "Withdrawal"
        verbose_name_plural = "Withdrawals"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["status"]),
            models.Index(fields=["reference"]),
        ]

    def __str__(self):
        return f"Withdrawal {self.reference} - ₦{self.amount} ({self.status})"

    def calculate_fee(self):
        """
        Calculate withdrawal fee based on tiered structure.
        Fee includes ₦50 Paystack fee + variable platform fee.

        Tiers:
        - ₦2,000 - ₦9,999: ₦100 (₦50 Paystack + ₦50 Platform)
        - ₦10,000 - ₦49,999: ₦150 (₦50 Paystack + ₦100 Platform)
        - ₦50,000 - ₦99,999: ₦200 (₦50 Paystack + ₦150 Platform)
        - ₦100,000 - ₦200,000: ₦250 (₦50 Paystack + ₦200 Platform)
        - ₦200,000+: ₦300 (₦50 Paystack + ₦250 Platform)
        """
        from decimal import Decimal

        amount = self.amount

        if amount < Decimal("10000.00"):
            # ₦2K - ₦9,999
            return Decimal("100.00")
        elif amount < Decimal("50000.00"):
            # ₦10K - ₦49,999
            return Decimal("150.00")
        elif amount < Decimal("100000.00"):
            # ₦50K - ₦99,999
            return Decimal("200.00")
        elif amount <= Decimal("200000.00"):
            # ₦100K - ₦200K
            return Decimal("250.00")
        else:
            # ₦200K+
            return Decimal("300.00")
