"""
Wallet Serializers
"""

from rest_framework import serializers
from .models import Wallet, WalletTransaction, BankAccount, Withdrawal
from users.models import CustomUser


class WalletSerializer(serializers.ModelSerializer):
    """
    Serializer for wallet balance and details.
    Balance is computed from transactions (read-only).
    """

    balance = serializers.SerializerMethodField()
    user_email = serializers.EmailField(source="user.email", read_only=True)
    user_name = serializers.CharField(source="user.full_name", read_only=True)

    class Meta:
        model = Wallet
        fields = [
            "id",
            "user_email",
            "user_name",
            "balance",
            "currency",
            "is_active",
            "created_at",
        ]
        read_only_fields = fields

    def get_balance(self, obj):
        """Return wallet balance as float"""
        return float(obj.balance)


class WalletTransactionSerializer(serializers.ModelSerializer):
    """
    Serializer for wallet transaction history.
    Shows all transaction details with formatted amounts.
    """

    amount_display = serializers.SerializerMethodField()
    balance_before_display = serializers.SerializerMethodField()
    balance_after_display = serializers.SerializerMethodField()
    transaction_type_display = serializers.CharField(
        source="get_transaction_type_display", read_only=True
    )

    class Meta:
        model = WalletTransaction
        fields = [
            "id",
            "transaction_type",
            "transaction_type_display",
            "amount",
            "amount_display",
            "balance_before",
            "balance_before_display",
            "balance_after",
            "balance_after_display",
            "reference",
            "description",
            "created_at",
        ]
        read_only_fields = fields

    def get_amount_display(self, obj):
        """Format amount with currency symbol"""
        return f"₦{obj.amount:,.2f}"

    def get_balance_before_display(self, obj):
        """Format balance_before with currency symbol"""
        return f"₦{obj.balance_before:,.2f}"

    def get_balance_after_display(self, obj):
        """Format balance_after with currency symbol"""
        return f"₦{obj.balance_after:,.2f}"


class WalletStatsSerializer(serializers.Serializer):
    """
    Serializer for wallet statistics.
    Shows aggregated transaction data.
    """

    total_credited = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_debited = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_refunded = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_transactions = serializers.IntegerField()
    last_transaction_date = serializers.DateTimeField(allow_null=True)


class FundWalletSerializer(serializers.Serializer):
    """
    Serializer for wallet funding request.
    This will be used in Phase 4 for Paystack integration.
    """

    amount = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=100.00,  # Minimum ₦100
        help_text="Amount to fund (minimum ₦100)",
    )

    def validate_amount(self, value):
        """Ensure amount is positive and reasonable"""
        if value < 100:
            raise serializers.ValidationError("Minimum funding amount is ₦100")
        if value > 1000000:  # Max ₦1M per transaction
            raise serializers.ValidationError(
                "Maximum funding amount is ₦1,000,000 per transaction"
            )
        return value


# ==============================================================================
# BANK ACCOUNT SERIALIZERS (Phase 4 - Withdrawals)
# ==============================================================================


class BankAccountSerializer(serializers.ModelSerializer):
    """
    Serializer for bank account management.
    """

    user_email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = BankAccount
        fields = [
            "id",
            "user_email",
            "bank_name",
            "bank_code",
            "account_number",
            "account_name",
            "is_verified",
            "is_default",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "user_email",
            "account_name",
            "is_verified",
            "created_at",
        ]

    def validate_account_number(self, value):
        """Validate account number is 10 digits"""
        if not value.isdigit():
            raise serializers.ValidationError("Account number must contain only digits")
        if len(value) != 10:
            raise serializers.ValidationError("Account number must be 10 digits")
        return value

    def validate(self, attrs):
        """Check for duplicate account (same account number AND bank)"""
        user = self.context["request"].user
        account_number = attrs.get("account_number")
        bank_code = attrs.get("bank_code")

        # Check if user already has this EXACT account (same number + same bank)
        # This allows same account number across different banks (e.g., OPay, Moniepoint using phone numbers)
        if BankAccount.objects.filter(
            user=user, account_number=account_number, bank_code=bank_code
        ).exists():
            raise serializers.ValidationError(
                f"You have already added this account for {attrs.get('bank_name')}"
            )

        return attrs


class WithdrawalSerializer(serializers.Serializer):
    """
    Serializer for withdrawal request.
    """

    amount = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=1000.00,  # Minimum ₦1,000
        help_text="Amount to withdraw (minimum ₦1,000)",
    )
    bank_account_id = serializers.UUIDField(
        help_text="ID of the bank account to withdraw to"
    )

    def validate_amount(self, value):
        """Validate withdrawal amount"""
        if value < 1000:
            raise serializers.ValidationError("Minimum withdrawal amount is ₦1,000")
        if value > 10000000:  # Max ₦10M per transaction
            raise serializers.ValidationError(
                "Maximum withdrawal amount is ₦10,000,000"
            )
        return value

    def validate_bank_account_id(self, value):
        """Validate bank account belongs to user"""
        user = self.context["request"].user

        try:
            bank_account = BankAccount.objects.get(id=value, user=user)
            if not bank_account.is_verified:
                raise serializers.ValidationError(
                    "Bank account not verified. Please verify your account first."
                )
        except BankAccount.DoesNotExist:
            raise serializers.ValidationError(
                "Bank account not found or does not belong to you"
            )

        return value

    def validate(self, attrs):
        """Validate user has sufficient balance"""
        user = self.context["request"].user
        amount = attrs["amount"]

        # Calculate tiered fee
        from decimal import Decimal

        if amount < Decimal("10000.00"):
            # ₦2K - ₦9,999: ₦100
            fee = Decimal("100.00")
        elif amount < Decimal("50000.00"):
            # ₦10K - ₦49,999: ₦150
            fee = Decimal("150.00")
        elif amount < Decimal("100000.00"):
            # ₦50K - ₦99,999: ₦200
            fee = Decimal("200.00")
        elif amount <= Decimal("200000.00"):
            # ₦100K - ₦200K: ₦250
            fee = Decimal("250.00")
        else:
            # ₦200K+: ₦300
            fee = Decimal("300.00")

        total_required = amount + fee

        # Check wallet balance
        if user.wallet.balance < total_required:
            raise serializers.ValidationError(
                f"Insufficient balance. You need ₦{total_required:,.2f} "
                f"(₦{amount:,.2f} + ₦{fee:,.2f} fee) but have ₦{user.wallet.balance:,.2f}"
            )

        return attrs


class WithdrawalHistorySerializer(serializers.ModelSerializer):
    """
    Serializer for withdrawal history display.
    """

    bank_account_details = serializers.SerializerMethodField()
    amount_display = serializers.SerializerMethodField()
    fee_display = serializers.SerializerMethodField()
    net_amount_display = serializers.SerializerMethodField()
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Withdrawal
        fields = [
            "id",
            "amount",
            "amount_display",
            "fee",
            "fee_display",
            "net_amount",
            "net_amount_display",
            "bank_account_details",
            "reference",
            "status",
            "status_display",
            "failure_reason",
            "created_at",
            "completed_at",
        ]
        read_only_fields = fields

    def get_bank_account_details(self, obj):
        """Get bank account details"""
        if obj.bank_account:
            return {
                "bank_name": obj.bank_account.bank_name,
                "account_number": obj.bank_account.account_number,
                "account_name": obj.bank_account.account_name,
            }
        return None

    def get_amount_display(self, obj):
        """Format amount"""
        return f"₦{obj.amount:,.2f}"

    def get_fee_display(self, obj):
        """Format fee"""
        return f"₦{obj.fee:,.2f}"

    def get_net_amount_display(self, obj):
        """Format net amount"""
        return f"₦{obj.net_amount:,.2f}"
