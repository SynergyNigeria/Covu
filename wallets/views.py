"""
Wallet API Views
"""

from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Sum, Count, Q
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from .models import Wallet, WalletTransaction, BankAccount, Withdrawal
from .serializers import (
    WalletSerializer,
    WalletTransactionSerializer,
    WalletStatsSerializer,
    FundWalletSerializer,
    BankAccountSerializer,
    WithdrawalSerializer,
    WithdrawalHistorySerializer,
)

import logging

logger = logging.getLogger(__name__)


class WalletView(generics.RetrieveAPIView):
    """
    Get wallet balance and details for authenticated user.

    GET /api/wallet/
    Returns wallet information including computed balance.
    """

    serializer_class = WalletSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        """Return authenticated user's wallet"""
        return self.request.user.wallet


class TransactionHistoryView(generics.ListAPIView):
    """
    List wallet transaction history for authenticated user.

    GET /api/wallet/transactions/
    Returns paginated list of transactions ordered by date (newest first).

    Query Parameters:
    - transaction_type: Filter by type (CREDIT, DEBIT, ESCROW_HOLD, etc.)
    - start_date: Filter transactions after this date (YYYY-MM-DD)
    - end_date: Filter transactions before this date (YYYY-MM-DD)
    """

    serializer_class = WalletTransactionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return user's transactions with optional filtering"""
        queryset = WalletTransaction.objects.filter(
            wallet=self.request.user.wallet
        ).order_by("-created_at")

        # Filter by transaction type
        transaction_type = self.request.query_params.get("transaction_type")
        if transaction_type:
            queryset = queryset.filter(transaction_type=transaction_type)

        # Filter by date range
        start_date = self.request.query_params.get("start_date")
        end_date = self.request.query_params.get("end_date")

        if start_date:
            queryset = queryset.filter(created_at__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__lte=end_date)

        return queryset


class WalletStatsView(APIView):
    """
    Get wallet statistics for authenticated user.

    GET /api/wallet/stats/
    Returns aggregated transaction data:
    - Total credited
    - Total debited
    - Total refunded
    - Total transaction count
    - Last transaction date
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        wallet = request.user.wallet

        # Get all transactions for this wallet
        transactions = WalletTransaction.objects.filter(wallet=wallet)

        # Calculate stats
        stats = {
            "total_credited": (
                transactions.filter(
                    Q(transaction_type="CREDIT") | Q(transaction_type="ESCROW_RELEASE")
                ).aggregate(total=Sum("amount"))["total"]
                or 0
            ),
            "total_debited": (
                transactions.filter(transaction_type="DEBIT").aggregate(
                    total=Sum("amount")
                )["total"]
                or 0
            ),
            "total_refunded": (
                transactions.filter(transaction_type="REFUND").aggregate(
                    total=Sum("amount")
                )["total"]
                or 0
            ),
            "total_transactions": transactions.count(),
            "last_transaction_date": (
                transactions.order_by("-created_at").first().created_at
                if transactions.exists()
                else None
            ),
        }

        serializer = WalletStatsSerializer(stats)
        return Response(serializer.data)


class FundWalletView(generics.CreateAPIView):
    """
    Fund wallet via Paystack.

    POST /api/wallet/fund/
    Body: { "amount": 5000.00 }

    Returns:
    {
        "status": "success",
        "message": "Payment initialized",
        "data": {
            "authorization_url": "https://checkout.paystack.com/...",
            "access_code": "...",
            "reference": "..."
        }
    }

    Frontend should redirect user to authorization_url to complete payment.
    Webhook will automatically credit wallet on successful payment.
    """

    serializer_class = FundWalletSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        from django.conf import settings
        import requests as http_requests
        import uuid

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        amount = serializer.validated_data["amount"]
        user = request.user

        # Convert amount to kobo (Paystack uses kobo, not naira)
        amount_in_kobo = int(amount * 100)

        # Generate unique reference
        reference = f"WALLET_FUND_{user.id}_{uuid.uuid4().hex[:12].upper()}"

        # Prepare Paystack request
        paystack_url = "https://api.paystack.co/transaction/initialize"
        headers = {
            "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
            "Content-Type": "application/json",
        }
        # Build a callback URL that points back to a backend return view.
        # Using request.build_absolute_uri + reverse ensures we generate an
        # absolute URL with the correct host (avoids localhost being used in
        # production when FRONTEND_URL is misconfigured).
        try:
            return_path = reverse("wallets:paystack-return", args=[reference])
            callback_absolute = request.build_absolute_uri(return_path)
        except Exception:
            # Fallback to frontend redirect if reverse fails
            callback_absolute = f"{settings.FRONTEND_URL}/templates/purchase.html?payment=success&ref={reference}"

        payload = {
            "email": user.email,
            "amount": amount_in_kobo,
            "reference": reference,
            "callback_url": callback_absolute,
            "metadata": {
                "user_id": str(user.id),
                "user_email": user.email,
                "wallet_id": str(user.wallet.id),
                "purpose": "wallet_funding",
            },
        }

        # Log callback and payload (without secrets) to help debug redirect issues
        try:
            logger.info(f"Paystack callback_url set to: {callback_absolute}")
            # Log minimal payload to avoid leaking secrets
            minimal_payload = {k: v for k, v in payload.items() if k != "metadata"}
            logger.info(f"Paystack init payload (minimal): {minimal_payload}")
        except Exception:
            pass

        try:
            # Initialize Paystack transaction
            response = http_requests.post(paystack_url, json=payload, headers=headers)
            response.raise_for_status()

            paystack_data = response.json()

            if paystack_data.get("status"):
                logger.info(
                    f"Paystack payment initialized: {user.email} - ₦{amount} - Ref: {reference}"
                )

                return Response(
                    {
                        "status": "success",
                        "message": "Payment initialized. Redirect user to authorization_url to complete payment.",
                        "data": {
                            "authorization_url": paystack_data["data"][
                                "authorization_url"
                            ],
                            "access_code": paystack_data["data"]["access_code"],
                            "reference": reference,
                            "amount": float(amount),
                        },
                    },
                    status=status.HTTP_200_OK,
                )
            else:
                logger.error(f"Paystack initialization failed: {paystack_data}")
                return Response(
                    {
                        "status": "error",
                        "message": "Failed to initialize payment",
                        "error": paystack_data.get("message", "Unknown error"),
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        except http_requests.exceptions.RequestException as e:
            logger.error(f"Paystack API error: {str(e)}")
            return Response(
                {
                    "status": "error",
                    "message": "Payment gateway error. Please try again.",
                    "error": str(e),
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )


class PaystackWebhookView(APIView):
    """
    Paystack Webhook Handler.

    POST /api/wallet/webhook/
    Receives payment notifications from Paystack.

    When payment is successful, automatically credits user's wallet.

    Security: Verifies webhook signature to prevent fraud.
    """

    permission_classes = []  # No authentication needed for webhook

    def post(self, request):
        from django.conf import settings
        import hmac
        import hashlib
        from django.db import transaction
        import uuid

        # Verify webhook signature
        signature = request.headers.get("X-Paystack-Signature")
        if not signature:
            logger.warning("Paystack webhook received without signature")
            return Response({"status": "error"}, status=status.HTTP_400_BAD_REQUEST)

        # Compute expected signature
        payload = request.body
        expected_signature = hmac.new(
            settings.PAYSTACK_SECRET_KEY.encode("utf-8"),
            payload,
            hashlib.sha512,
        ).hexdigest()

        # Verify signature matches
        if signature != expected_signature:
            logger.warning("Paystack webhook signature mismatch")
            return Response({"status": "error"}, status=status.HTTP_401_UNAUTHORIZED)

        # Parse webhook data
        data = request.data
        event = data.get("event")

        logger.info(f"Paystack webhook received: {event}")

        # Handle successful charge
        if event == "charge.success":
            payment_data = data.get("data", {})
            reference = payment_data.get("reference")
            amount_in_kobo = payment_data.get("amount")
            metadata = payment_data.get("metadata", {})

            # Extract user info from metadata
            user_id = metadata.get("user_id")
            wallet_id = metadata.get("wallet_id")

            if not user_id or not wallet_id:
                logger.error(f"Webhook missing user/wallet ID: {reference}")
                return Response({"status": "error"}, status=status.HTTP_400_BAD_REQUEST)

            # Convert kobo to naira
            amount = amount_in_kobo / 100

            try:
                with transaction.atomic():
                    # Get wallet
                    wallet = Wallet.objects.select_for_update().get(id=wallet_id)

                    # Check if transaction already processed (idempotency)
                    existing = WalletTransaction.objects.filter(
                        reference=reference
                    ).exists()
                    if existing:
                        logger.info(f"Transaction already processed: {reference}")
                        return Response({"status": "success"})

                    # Get current balance
                    balance_before = wallet.balance

                    # Create CREDIT transaction
                    WalletTransaction.objects.create(
                        wallet=wallet,
                        transaction_type="CREDIT",
                        amount=amount,
                        balance_before=balance_before,
                        balance_after=balance_before + amount,
                        reference=reference,
                        description=f"Wallet funding via Paystack - {reference}",
                    )

                    logger.info(
                        f"Wallet credited: {wallet.user.email} - ₦{amount:,.2f} - Ref: {reference}"
                    )

                    # Send email notification
                    try:
                        from notifications.email_service import EmailNotificationService

                        EmailNotificationService.send_wallet_funded(
                            user=wallet.user, amount=amount, reference=reference
                        )
                    except Exception as e:
                        logger.error(f"Failed to send email notification: {e}")

                    return Response({"status": "success"}, status=status.HTTP_200_OK)

            except Wallet.DoesNotExist:
                logger.error(f"Wallet not found: {wallet_id}")
                return Response({"status": "error"}, status=status.HTTP_404_NOT_FOUND)
            except Exception as e:
                logger.error(f"Error processing webhook: {str(e)}")
                return Response(
                    {"status": "error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        # Return success for all other events
        return Response({"status": "success"}, status=status.HTTP_200_OK)


class PaystackReturnView(APIView):
    """
    Handles browser redirects from Paystack after payment completion.

    This endpoint verifies the transaction with Paystack (like
    `VerifyPaymentView`) and then redirects the user back to the frontend
    with a short query string indicating success/failure. This avoids
    relying on FRONTEND_URL being correctly set in the environment and
    ensures the user is returned to the site after payment.
    """

    permission_classes = []

    def get(self, request, reference):
        from django.conf import settings
        import requests as http_requests
        from django.db import transaction

        paystack_url = f"https://api.paystack.co/transaction/verify/{reference}"
        headers = {"Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}"}

        try:
            response = http_requests.get(paystack_url, headers=headers, timeout=10)
            response.raise_for_status()
            paystack_data = response.json()

            success = False
            if paystack_data.get("status"):
                data = paystack_data.get("data", {})
                if data.get("status") == "success":
                    # Try to credit wallet (idempotent)
                    metadata = data.get("metadata", {})
                    wallet_id = metadata.get("wallet_id")

                    if wallet_id:
                        try:
                            with transaction.atomic():
                                from .models import Wallet, WalletTransaction

                                wallet = Wallet.objects.select_for_update().get(
                                    id=wallet_id
                                )
                                reference_exists = WalletTransaction.objects.filter(
                                    reference=reference
                                ).exists()
                                if not reference_exists:
                                    amount = data.get("amount", 0) / 100.0
                                    balance_before = wallet.balance
                                    WalletTransaction.objects.create(
                                        wallet=wallet,
                                        transaction_type="CREDIT",
                                        amount=amount,
                                        balance_before=balance_before,
                                        balance_after=balance_before + amount,
                                        reference=reference,
                                        description=f"Wallet funding via Paystack - {reference}",
                                    )
                                    success = True
                                else:
                                    # Already processed
                                    success = True
                        except Exception:
                            # Verification succeeded but DB update failed - still redirect
                            success = True

            # Redirect back to frontend with a query param the frontend knows to handle
            frontend_success_url = f"{settings.FRONTEND_URL}/templates/purchase.html?payment={'success' if success else 'failed'}&ref={reference}"
            return redirect(frontend_success_url)

        except Exception as e:
            # Always redirect user back to frontend; the webhook or manual
            # verification can reconcile the payment asynchronously.
            frontend_fail_url = f"{settings.FRONTEND_URL}/templates/purchase.html?payment=failed&ref={reference}"
            return redirect(frontend_fail_url)


class VerifyPaymentView(APIView):
    """
    Manually verify a Paystack payment.

    GET /api/wallet/verify/{reference}/
    Verifies payment status with Paystack and credits wallet if successful.

    Useful as fallback if webhook fails.

    UPDATED: Authentication is optional - the reference contains user_id in metadata
    This prevents auto-logout issues when user returns from Paystack after token expiry.
    """

    permission_classes = (
        []
    )  # No authentication required - we verify via reference metadata

    def get(self, request, reference):
        from django.conf import settings
        import requests as http_requests
        from django.db import transaction

        # Verify payment with Paystack
        paystack_url = f"https://api.paystack.co/transaction/verify/{reference}"
        headers = {"Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}"}

        try:
            response = http_requests.get(paystack_url, headers=headers)
            response.raise_for_status()

            paystack_data = response.json()

            if not paystack_data.get("status"):
                return Response(
                    {
                        "status": "error",
                        "message": "Payment verification failed",
                        "error": paystack_data.get("message"),
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            data = paystack_data.get("data", {})
            payment_status = data.get("status")
            amount_in_kobo = data.get("amount")
            metadata = data.get("metadata", {})

            # Check if payment was successful
            if payment_status != "success":
                return Response(
                    {
                        "status": "error",
                        "message": f"Payment status: {payment_status}",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Convert kobo to naira - IMPORTANT: Convert to Decimal for database operations
            from decimal import Decimal

            amount = Decimal(str(amount_in_kobo / 100))

            # Get user from metadata (not from request.user since auth is optional)
            user_id = metadata.get("user_id")
            wallet_id = metadata.get("wallet_id")

            if not user_id or not wallet_id:
                logger.error(
                    f"Missing user_id or wallet_id in payment metadata: {reference}"
                )
                return Response(
                    {"status": "error", "message": "Invalid payment reference"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # If user is authenticated, verify they own this transaction
            if request.user.is_authenticated:
                if str(request.user.id) != str(user_id):
                    logger.warning(
                        f"Authenticated user {request.user.id} trying to verify payment for user {user_id}"
                    )
                    return Response(
                        {"status": "error", "message": "Unauthorized"},
                        status=status.HTTP_403_FORBIDDEN,
                    )

            # Credit wallet
            with transaction.atomic():
                wallet = Wallet.objects.select_for_update().get(id=wallet_id)

                # Check if already processed
                existing = WalletTransaction.objects.filter(
                    reference=reference
                ).exists()
                if existing:
                    return Response(
                        {
                            "status": "success",
                            "message": "Payment already processed",
                            "amount": float(amount),
                            "balance": float(wallet.balance),
                        }
                    )

                balance_before = wallet.balance

                # Create CREDIT transaction
                WalletTransaction.objects.create(
                    wallet=wallet,
                    transaction_type="CREDIT",
                    amount=amount,
                    balance_before=balance_before,
                    balance_after=balance_before + amount,
                    reference=reference,
                    description=f"Wallet funding via Paystack (manual verification) - {reference}",
                )

                user_email = wallet.user.email
                logger.info(
                    f"Wallet credited (manual): {user_email} - ₦{amount:,.2f} - Ref: {reference}"
                )

                # Send email notification
                try:
                    from notifications.email_service import EmailNotificationService

                    EmailNotificationService.send_wallet_funded(
                        user=wallet.user, amount=amount, reference=reference
                    )
                except Exception as e:
                    logger.error(f"Failed to send email notification: {e}")

                return Response(
                    {
                        "status": "success",
                        "message": "Payment verified and wallet credited",
                        "amount": float(amount),
                        "new_balance": float(wallet.balance),
                    },
                    status=status.HTTP_200_OK,
                )

        except http_requests.exceptions.RequestException as e:
            logger.error(f"Paystack verification error: {str(e)}")
            return Response(
                {
                    "status": "error",
                    "message": "Payment gateway error",
                    "error": str(e),
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )


# ==============================================================================
# BANK ACCOUNT VIEWS (Phase 4 - Withdrawals)
# ==============================================================================


class NigerianBanksView(APIView):
    """
    Get list of Nigerian banks from Paystack.

    GET /api/wallet/banks/
    Returns list of all Nigerian banks with codes.
    No authentication required (public endpoint).
    """

    permission_classes = []  # Public endpoint

    def get(self, request):
        from django.conf import settings
        import requests as http_requests

        try:
            paystack_url = "https://api.paystack.co/bank?country=nigeria"
            headers = {"Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}"}

            response = http_requests.get(paystack_url, headers=headers)
            response.raise_for_status()

            paystack_data = response.json()

            if paystack_data.get("status"):
                banks = paystack_data.get("data", [])
                return Response(
                    {"status": "success", "data": banks}, status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {
                        "status": "error",
                        "message": "Failed to fetch banks from Paystack",
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        except http_requests.exceptions.RequestException as e:
            logger.error(f"Error fetching banks from Paystack: {str(e)}")
            return Response(
                {"status": "error", "message": "Could not fetch bank list"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class BankAccountListCreateView(generics.ListCreateAPIView):
    """
    List and create bank accounts for withdrawals.

    GET /api/wallet/bank-accounts/
    Returns list of user's bank accounts.

    POST /api/wallet/bank-accounts/
    Body: {
        "bank_name": "GTBank",
        "bank_code": "058",
        "account_number": "0123456789",
        "is_default": true
    }

    Creates new bank account with Paystack verification.
    """

    serializer_class = BankAccountSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return user's bank accounts"""
        return BankAccount.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        """Verify account with Paystack before saving"""
        from django.conf import settings
        import requests as http_requests

        bank_code = serializer.validated_data["bank_code"]
        account_number = serializer.validated_data["account_number"]
        user = self.request.user

        # Verify account with Paystack
        paystack_url = "https://api.paystack.co/bank/resolve"
        headers = {"Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}"}
        params = {"account_number": account_number, "bank_code": bank_code}

        try:
            response = http_requests.get(paystack_url, headers=headers, params=params)
            response.raise_for_status()

            paystack_data = response.json()

            if paystack_data.get("status"):
                account_name = paystack_data["data"]["account_name"]

                # Save account with verified name
                bank_account = serializer.save(
                    user=user, account_name=account_name, is_verified=True
                )

                # Create Paystack transfer recipient
                recipient_url = "https://api.paystack.co/transferrecipient"
                recipient_payload = {
                    "type": "nuban",
                    "name": account_name,
                    "account_number": account_number,
                    "bank_code": bank_code,
                    "currency": "NGN",
                    "metadata": {
                        "user_id": str(user.id),
                        "user_email": user.email,
                    },
                }

                recipient_response = http_requests.post(
                    recipient_url, json=recipient_payload, headers=headers
                )

                if recipient_response.status_code == 201:
                    recipient_data = recipient_response.json()
                    recipient_code = recipient_data["data"]["recipient_code"]

                    # Update with recipient code
                    bank_account.paystack_recipient_code = recipient_code
                    bank_account.save()

                    logger.info(
                        f"Bank account verified and recipient created: "
                        f"{user.email} - {account_name} ({account_number})"
                    )
                elif recipient_response.status_code == 400:
                    # Handle duplicate recipient (Paystack already has this account)
                    try:
                        error_data = recipient_response.json()
                        error_message = error_data.get("message", "")

                        # If recipient already exists, try to fetch it
                        if (
                            "already" in error_message.lower()
                            or "duplicate" in error_message.lower()
                        ):
                            logger.info(
                                f"Recipient already exists for {account_number}, fetching existing recipient..."
                            )

                            # Try to find existing recipient by listing recipients
                            list_url = (
                                f"https://api.paystack.co/transferrecipient?perPage=100"
                            )
                            list_response = http_requests.get(list_url, headers=headers)

                            if list_response.status_code == 200:
                                list_data = list_response.json()
                                recipients = list_data.get("data", [])

                                # Find matching recipient
                                matching_recipient = None
                                for recipient in recipients:
                                    if (
                                        recipient.get("details", {}).get(
                                            "account_number"
                                        )
                                        == account_number
                                        and recipient.get("details", {}).get(
                                            "bank_code"
                                        )
                                        == bank_code
                                    ):
                                        matching_recipient = recipient
                                        break

                                if matching_recipient:
                                    bank_account.paystack_recipient_code = (
                                        matching_recipient["recipient_code"]
                                    )
                                    bank_account.save()
                                    logger.info(
                                        f"Using existing recipient: {matching_recipient['recipient_code']}"
                                    )
                                else:
                                    logger.warning(
                                        f"Could not find existing recipient for {account_number}"
                                    )
                            else:
                                logger.warning(
                                    f"Failed to list recipients: {list_response.text}"
                                )
                        else:
                            logger.warning(
                                f"Recipient creation failed: {error_message}"
                            )
                    except Exception as e:
                        logger.error(f"Error handling duplicate recipient: {str(e)}")
                else:
                    logger.warning(
                        f"Recipient creation failed but account verified: "
                        f"{account_number} - {recipient_response.text}"
                    )

            else:
                raise serializers.ValidationError(
                    "Could not verify bank account. Please check account number and bank code."
                )

        except http_requests.exceptions.RequestException as e:
            logger.error(f"Paystack account verification error: {str(e)}")
            raise serializers.ValidationError(
                "Bank verification service unavailable. Please try again."
            )


class BankAccountDetailView(generics.RetrieveDestroyAPIView):
    """
    Retrieve or delete a bank account.

    GET /api/wallet/bank-accounts/{id}/
    Returns bank account details.

    DELETE /api/wallet/bank-accounts/{id}/
    Deletes bank account (if not default or has pending withdrawals).
    """

    serializer_class = BankAccountSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return user's bank accounts"""
        return BankAccount.objects.filter(user=self.request.user)

    def perform_destroy(self, instance):
        """Check before deleting"""
        # Check for pending withdrawals
        pending_withdrawals = Withdrawal.objects.filter(
            bank_account=instance, status__in=["PENDING", "PROCESSING"]
        ).exists()

        if pending_withdrawals:
            raise serializers.ValidationError(
                "Cannot delete bank account with pending withdrawals"
            )

        instance.delete()


# ==============================================================================
# WITHDRAWAL VIEWS (Phase 4)
# ==============================================================================


class WithdrawFundsView(generics.CreateAPIView):
    """
    Request withdrawal to bank account.

    POST /api/wallet/withdraw/
    Body: {
        "amount": 10000.00,
        "bank_account_id": "uuid-here"
    }

    Initiates Paystack transfer and debits wallet on success.
    """

    serializer_class = WithdrawalSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        from django.conf import settings
        import requests as http_requests
        from django.db import transaction as db_transaction
        import uuid
        from decimal import Decimal

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        amount = serializer.validated_data["amount"]
        bank_account_id = serializer.validated_data["bank_account_id"]
        user = request.user

        # Get bank account
        try:
            bank_account = BankAccount.objects.get(id=bank_account_id, user=user)
        except BankAccount.DoesNotExist:
            return Response(
                {"status": "error", "message": "Bank account not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Calculate tiered fee
        if amount < Decimal("10000.00"):
            # ₦2K - ₦9,999: ₦100 (₦50 Paystack + ₦50 Platform)
            fee = Decimal("100.00")
        elif amount < Decimal("50000.00"):
            # ₦10K - ₦49,999: ₦150 (₦50 Paystack + ₦100 Platform)
            fee = Decimal("150.00")
        elif amount < Decimal("100000.00"):
            # ₦50K - ₦99,999: ₦200 (₦50 Paystack + ₦150 Platform)
            fee = Decimal("200.00")
        elif amount <= Decimal("200000.00"):
            # ₦100K - ₦200K: ₦250 (₦50 Paystack + ₦200 Platform)
            fee = Decimal("250.00")
        else:
            # ₦200K+: ₦300 (₦50 Paystack + ₦250 Platform)
            fee = Decimal("300.00")

        net_amount = amount - fee

        # Generate unique reference
        reference = f"WITHDRAWAL_{user.id}_{uuid.uuid4().hex[:12].upper()}"

        try:
            with db_transaction.atomic():
                wallet = Wallet.objects.select_for_update().get(user=user)

                # Double-check balance
                total_required = amount + fee
                if wallet.balance < total_required:
                    return Response(
                        {
                            "status": "error",
                            "message": f"Insufficient balance. Need ₦{total_required:,.2f}",
                            "balance": float(wallet.balance),
                            "amount": float(amount),
                            "fee": float(fee),
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                # Create withdrawal record
                withdrawal = Withdrawal.objects.create(
                    user=user,
                    wallet=wallet,
                    bank_account=bank_account,
                    amount=amount,
                    fee=fee,
                    net_amount=net_amount,
                    reference=reference,
                    status="PENDING",
                )

                # Check if bank account has recipient code
                if not bank_account.paystack_recipient_code:
                    withdrawal.status = "FAILED"
                    withdrawal.failure_reason = (
                        "Bank account not properly configured with Paystack"
                    )
                    withdrawal.save()

                    return Response(
                        {
                            "status": "error",
                            "message": "Bank account not properly configured. Please delete and re-add this account.",
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                # Initiate Paystack transfer
                paystack_url = "https://api.paystack.co/transfer"
                headers = {
                    "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
                    "Content-Type": "application/json",
                }

                # Convert to kobo
                amount_in_kobo = int(net_amount * 100)

                payload = {
                    "source": "balance",
                    "reason": f"Withdrawal - {reference}",
                    "amount": amount_in_kobo,
                    "recipient": bank_account.paystack_recipient_code,
                    "reference": reference,
                    "metadata": {
                        "user_id": str(user.id),
                        "user_email": user.email,
                        "withdrawal_id": str(withdrawal.id),
                    },
                }

                logger.info(f"Initiating Paystack transfer: {payload}")

                response = http_requests.post(
                    paystack_url, json=payload, headers=headers
                )

                # Log response for debugging
                logger.info(f"Paystack response status: {response.status_code}")
                logger.info(f"Paystack response body: {response.text}")

                response.raise_for_status()

                paystack_data = response.json()

                if paystack_data.get("status"):
                    transfer_data = paystack_data["data"]

                    # Update withdrawal with Paystack data
                    withdrawal.paystack_transfer_code = transfer_data.get(
                        "transfer_code"
                    )
                    withdrawal.paystack_transfer_id = transfer_data.get("id")
                    withdrawal.status = "PROCESSING"
                    withdrawal.save()

                    # Debit wallet (create WITHDRAWAL transaction)
                    balance_before = wallet.balance

                    wallet_transaction = WalletTransaction.objects.create(
                        wallet=wallet,
                        transaction_type="WITHDRAWAL",
                        amount=total_required,  # Amount + fee
                        balance_before=balance_before,
                        balance_after=balance_before - total_required,
                        reference=reference,
                        description=f"Withdrawal to {bank_account.bank_name} ({bank_account.account_number}) - {reference}",
                        metadata={
                            "withdrawal_id": str(withdrawal.id),
                            "bank_account": bank_account.account_number,
                            "fee": str(fee),
                            "net_amount": str(net_amount),
                        },
                    )

                    withdrawal.wallet_transaction = wallet_transaction
                    withdrawal.save()

                    logger.info(
                        f"Withdrawal initiated: {user.email} - ₦{amount:,.2f} - Ref: {reference}"
                    )

                    # Send email notification
                    try:
                        from notifications.email_service import EmailNotificationService

                        EmailNotificationService.send_withdrawal_initiated(
                            user=user,
                            amount=amount,
                            account_number=bank_account.account_number,
                            bank_name=bank_account.bank_name,
                            reference=reference,
                        )
                    except Exception as e:
                        logger.error(f"Failed to send email notification: {e}")

                    return Response(
                        {
                            "status": "success",
                            "message": "Withdrawal initiated successfully",
                            "data": {
                                "reference": reference,
                                "amount": float(amount),
                                "fee": float(fee),
                                "net_amount": float(net_amount),
                                "bank_account": {
                                    "bank_name": bank_account.bank_name,
                                    "account_number": bank_account.account_number,
                                    "account_name": bank_account.account_name,
                                },
                                "status": "PROCESSING",
                                "new_balance": float(wallet.balance),
                            },
                        },
                        status=status.HTTP_200_OK,
                    )
                else:
                    withdrawal.status = "FAILED"
                    withdrawal.failure_reason = paystack_data.get(
                        "message", "Unknown error"
                    )
                    withdrawal.save()

                    return Response(
                        {
                            "status": "error",
                            "message": "Transfer initiation failed",
                            "error": paystack_data.get("message"),
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

        except http_requests.exceptions.RequestException as e:
            logger.error(f"Paystack transfer error: {str(e)}")

            # Mark withdrawal as failed
            if "withdrawal" in locals():
                withdrawal.status = "FAILED"
                withdrawal.failure_reason = str(e)
                withdrawal.save()

            # Check for specific Paystack errors
            error_message = "Transfer service unavailable. Please try again."

            # Parse Paystack error response
            try:
                if hasattr(e.response, "json"):
                    error_data = e.response.json()
                    paystack_message = error_data.get("message", "")

                    # Check for business upgrade requirement
                    if (
                        "starter business" in paystack_message.lower()
                        or "upgrade" in paystack_message.lower()
                    ):
                        error_message = "Withdrawals are temporarily unavailable. Your Paystack account needs to be upgraded to a Registered Business. Please contact support."
                    elif paystack_message:
                        error_message = paystack_message
            except:
                pass

            return Response(
                {
                    "status": "error",
                    "message": error_message,
                    "error": str(e),
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )


class WithdrawalHistoryView(generics.ListAPIView):
    """
    List withdrawal history for authenticated user.

    GET /api/wallet/withdrawals/
    Returns paginated list of withdrawals ordered by date (newest first).

    Query Parameters:
    - status: Filter by status (PENDING, PROCESSING, SUCCESS, FAILED)
    """

    serializer_class = WithdrawalHistorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return user's withdrawals with optional filtering"""
        queryset = (
            Withdrawal.objects.filter(user=self.request.user)
            .select_related("bank_account")
            .order_by("-created_at")
        )

        # Filter by status
        status_filter = self.request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter.upper())

        return queryset


class TransferWebhookView(APIView):
    """
    Paystack Transfer Webhook Handler.

    POST /api/wallet/transfer-webhook/
    Receives transfer status updates from Paystack.

    Updates withdrawal status and sends email notifications.
    """

    permission_classes = []  # No authentication for webhook

    def post(self, request):
        from django.conf import settings
        import hmac
        import hashlib
        from django.utils import timezone

        # Verify webhook signature
        signature = request.headers.get("X-Paystack-Signature")
        if not signature:
            logger.warning("Transfer webhook received without signature")
            return Response({"status": "error"}, status=status.HTTP_400_BAD_REQUEST)

        # Compute expected signature
        payload = request.body
        expected_signature = hmac.new(
            settings.PAYSTACK_SECRET_KEY.encode("utf-8"), payload, hashlib.sha512
        ).hexdigest()

        # Verify signature matches
        if signature != expected_signature:
            logger.warning("Transfer webhook signature mismatch")
            return Response({"status": "error"}, status=status.HTTP_401_UNAUTHORIZED)

        # Parse webhook data
        data = request.data
        event = data.get("event")

        logger.info(f"Transfer webhook received: {event}")

        # Handle transfer success/failure
        if event in ["transfer.success", "transfer.failed"]:
            transfer_data = data.get("data", {})
            reference = transfer_data.get("reference")
            transfer_status = transfer_data.get("status")

            if not reference:
                logger.error("Transfer webhook missing reference")
                return Response({"status": "error"}, status=status.HTTP_400_BAD_REQUEST)

            try:
                withdrawal = Withdrawal.objects.get(reference=reference)

                if event == "transfer.success" and transfer_status == "success":
                    withdrawal.status = "SUCCESS"
                    withdrawal.completed_at = timezone.now()
                    withdrawal.save()

                    logger.info(
                        f"Withdrawal completed: {reference} - ₦{withdrawal.amount:,.2f}"
                    )

                    # Send success email
                    try:
                        from notifications.email_service import EmailNotificationService

                        EmailNotificationService.send_withdrawal_completed(
                            user=withdrawal.user,
                            amount=withdrawal.amount,
                            account_number=withdrawal.bank_account.account_number,
                            bank_name=withdrawal.bank_account.bank_name,
                            reference=reference,
                        )
                    except Exception as e:
                        logger.error(f"Failed to send email notification: {e}")

                elif event == "transfer.failed" or transfer_status in [
                    "failed",
                    "reversed",
                ]:
                    withdrawal.status = "FAILED"
                    withdrawal.failure_reason = transfer_data.get(
                        "failure_reason", "Transfer failed"
                    )
                    withdrawal.completed_at = timezone.now()
                    withdrawal.save()

                    logger.warning(
                        f"Withdrawal failed: {reference} - {withdrawal.failure_reason}"
                    )

                    # Refund wallet (credit back)
                    if withdrawal.wallet_transaction:
                        from django.db import transaction as db_transaction

                        with db_transaction.atomic():
                            wallet = Wallet.objects.select_for_update().get(
                                user=withdrawal.user
                            )
                            balance_before = wallet.balance
                            refund_amount = withdrawal.amount + withdrawal.fee

                            WalletTransaction.objects.create(
                                wallet=wallet,
                                transaction_type="CREDIT",
                                amount=refund_amount,
                                balance_before=balance_before,
                                balance_after=balance_before + refund_amount,
                                reference=f"REFUND_{reference}",
                                description=f"Withdrawal failed - funds returned - {reference}",
                                metadata={
                                    "withdrawal_id": str(withdrawal.id),
                                    "original_reference": reference,
                                },
                            )

                    # Send failure email
                    try:
                        from notifications.email_service import EmailNotificationService

                        EmailNotificationService.send_withdrawal_failed(
                            user=withdrawal.user,
                            amount=withdrawal.amount,
                            reference=reference,
                            reason=withdrawal.failure_reason,
                        )
                    except Exception as e:
                        logger.error(f"Failed to send email notification: {e}")

                return Response({"status": "success"}, status=status.HTTP_200_OK)

            except Withdrawal.DoesNotExist:
                logger.error(f"Withdrawal not found: {reference}")
                return Response({"status": "error"}, status=status.HTTP_404_NOT_FOUND)

        # Return success for all other events
        return Response({"status": "success"}, status=status.HTTP_200_OK)


# ==============================================================================
# NIGERIAN BANKS LIST (from Paystack)
# ==============================================================================


class NigerianBanksView(APIView):
    """
    Get list of all Nigerian banks from Paystack.

    GET /api/wallet/banks/
    Returns list of banks with name and code.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Fetch Nigerian banks from Paystack"""
        from django.conf import settings
        import requests as http_requests

        try:
            paystack_url = "https://api.paystack.co/bank"
            headers = {"Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}"}
            params = {"country": "nigeria", "perPage": 100}

            response = http_requests.get(
                paystack_url, headers=headers, params=params, timeout=10
            )
            response.raise_for_status()

            paystack_data = response.json()

            if paystack_data.get("status"):
                banks = paystack_data.get("data", [])
                # Sort banks alphabetically
                banks_sorted = sorted(banks, key=lambda x: x.get("name", ""))

                return Response(
                    {
                        "status": "success",
                        "data": [
                            {
                                "name": bank.get("name"),
                                "code": bank.get("code"),
                                "slug": bank.get("slug"),
                            }
                            for bank in banks_sorted
                        ],
                    },
                    status=status.HTTP_200_OK,
                )
            else:
                return Response(
                    {"status": "error", "message": "Failed to fetch banks"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        except http_requests.exceptions.RequestException as e:
            logger.error(f"Error fetching banks from Paystack: {str(e)}")
            return Response(
                {
                    "status": "error",
                    "message": "Unable to fetch bank list. Please try again.",
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )


# ==============================================================================
# LEGACY WITHDRAW VIEW (Deprecated - use WithdrawFundsView)
# ==============================================================================


class WithdrawView(generics.CreateAPIView):
    """
    DEPRECATED: Use WithdrawFundsView instead.

    Legacy endpoint for backward compatibility.
    Redirects to new withdrawal implementation.
    """

    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        return Response(
            {
                "message": "This endpoint is deprecated. Use POST /api/wallet/withdraw/ instead",
                "new_endpoint": "/api/wallet/withdraw/",
                "documentation": "See PHASE-4-API-REFERENCE.md for details",
            },
            status=status.HTTP_410_GONE,  # Gone
        )
