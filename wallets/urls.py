"""
Wallet URL Configuration
"""

from django.urls import path
from .views import (
    WalletView,
    TransactionHistoryView,
    WalletStatsView,
    FundWalletView,
    PaystackWebhookView,
    VerifyPaymentView,
    WithdrawView,  # Legacy - deprecated
    # Phase 4 - Withdrawal endpoints
    BankAccountListCreateView,
    BankAccountDetailView,
    WithdrawFundsView,
    WithdrawalHistoryView,
    TransferWebhookView,
)

app_name = "wallets"

urlpatterns = [
    # Wallet operations
    path("", WalletView.as_view(), name="wallet-detail"),
    path("transactions/", TransactionHistoryView.as_view(), name="transaction-history"),
    path("stats/", WalletStatsView.as_view(), name="wallet-stats"),
    # Paystack funding (Phase 3)
    path("fund/", FundWalletView.as_view(), name="fund-wallet"),
    path("webhook/", PaystackWebhookView.as_view(), name="paystack-webhook"),
    path("verify/<str:reference>/", VerifyPaymentView.as_view(), name="verify-payment"),
    # Bank account management (Phase 4)
    path("bank-accounts/", BankAccountListCreateView.as_view(), name="bank-accounts"),
    path(
        "bank-accounts/<uuid:pk>/",
        BankAccountDetailView.as_view(),
        name="bank-account-detail",
    ),
    # Withdrawals (Phase 4)
    path("withdraw/", WithdrawFundsView.as_view(), name="withdraw-funds"),
    path("withdrawals/", WithdrawalHistoryView.as_view(), name="withdrawal-history"),
    path("transfer-webhook/", TransferWebhookView.as_view(), name="transfer-webhook"),
    # Legacy (deprecated)
    # path("withdraw-old/", WithdrawView.as_view(), name="withdraw-old"),
]
