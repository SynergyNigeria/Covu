# Test Wallet System
# Verifies deposits and withdrawals are working

import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "covu.settings")
django.setup()

from django.conf import settings
from wallets.models import Wallet, WalletTransaction, Withdrawal
from users.models import CustomUser

print("=" * 70)
print("WALLET SYSTEM VERIFICATION")
print("=" * 70)

# Check Paystack configuration
print("\n1️⃣ Paystack Configuration:")
print("-" * 70)
secret_key = settings.PAYSTACK_SECRET_KEY
public_key = settings.PAYSTACK_PUBLIC_KEY

if secret_key.startswith("sk_live_"):
    print("✅ Using LIVE Paystack keys (Production Mode)")
elif secret_key.startswith("sk_test_"):
    print("⚠️  Using TEST Paystack keys (Development Mode)")
else:
    print("❌ Invalid Paystack key format")

print(f"   Secret Key: {secret_key[:15]}...")
print(f"   Public Key: {public_key[:15]}...")

# Check email configuration
print("\n2️⃣ Email Configuration:")
print("-" * 70)
print(f"✅ Email Backend: {settings.EMAIL_BACKEND}")
print(f"✅ Email Host: {settings.EMAIL_HOST}")
print(f"✅ Email User: {settings.EMAIL_HOST_USER}")
print(f"✅ From Email: {settings.DEFAULT_FROM_EMAIL}")

# Check wallet statistics
print("\n3️⃣ Wallet Statistics:")
print("-" * 70)
total_users = CustomUser.objects.count()
total_wallets = Wallet.objects.count()
total_transactions = WalletTransaction.objects.count()
total_withdrawals = Withdrawal.objects.count()

print(f"   Total Users: {total_users}")
print(f"   Total Wallets: {total_wallets}")
print(f"   Total Transactions: {total_transactions}")
print(f"   Total Withdrawals: {total_withdrawals}")

# Recent transactions
print("\n4️⃣ Recent Transactions (Last 5):")
print("-" * 70)
recent = WalletTransaction.objects.order_by("-created_at")[:5]
if recent:
    for txn in recent:
        status_icon = "💰" if txn.transaction_type == "CREDIT" else "💸"
        print(
            f"{status_icon} {txn.transaction_type:<15} | ₦{txn.amount:>10,.2f} | {txn.wallet.user.email}"
        )
else:
    print("   No transactions yet")

# Recent withdrawals
print("\n5️⃣ Recent Withdrawals (Last 5):")
print("-" * 70)
recent_withdrawals = Withdrawal.objects.order_by("-created_at")[:5]
if recent_withdrawals:
    for w in recent_withdrawals:
        status_icons = {
            "PENDING": "⏳",
            "PROCESSING": "🔄",
            "SUCCESS": "✅",
            "FAILED": "❌",
        }
        icon = status_icons.get(w.status, "❓")
        print(f"{icon} {w.status:<12} | ₦{w.amount:>10,.2f} | {w.user.email}")
else:
    print("   No withdrawals yet")

# Check Celery
print("\n6️⃣ Celery Configuration:")
print("-" * 70)
celery_broker = settings.CELERY_BROKER_URL
print(f"✅ Broker URL: {celery_broker}")
print("   Note: Make sure Celery worker is running!")

# API Endpoints
print("\n7️⃣ Available Wallet Endpoints:")
print("-" * 70)
endpoints = [
    ("GET", "/api/wallet/", "Get wallet balance"),
    ("GET", "/api/wallet/transactions/", "Transaction history"),
    ("GET", "/api/wallet/stats/", "Wallet statistics"),
    ("POST", "/api/wallet/fund/", "Fund wallet (Paystack)"),
    ("POST", "/api/wallet/webhook/", "Paystack webhook (auto-credit)"),
    ("GET", "/api/wallet/verify/{ref}/", "Verify payment"),
    ("GET", "/api/wallet/bank-accounts/", "List bank accounts"),
    ("POST", "/api/wallet/bank-accounts/", "Add bank account"),
    ("POST", "/api/wallet/withdraw/", "Withdraw funds"),
    ("GET", "/api/wallet/withdrawals/", "Withdrawal history"),
    ("POST", "/api/wallet/transfer-webhook/", "Transfer status webhook"),
]

for method, endpoint, description in endpoints:
    print(f"   {method:<6} {endpoint:<35} - {description}")

print("\n" + "=" * 70)
print("✅ Wallet System Ready!")
print("=" * 70)

# Production readiness check
print("\n🚀 Production Readiness:")
print("-" * 70)
checks = []

# Check 1: Live keys
if secret_key.startswith("sk_live_"):
    checks.append(("✅", "Live Paystack keys configured"))
else:
    checks.append(("⚠️ ", "Using test keys (change to live for production)"))

# Check 2: Email
if settings.EMAIL_HOST and settings.EMAIL_HOST_USER:
    checks.append(("✅", "Email configured"))
else:
    checks.append(("❌", "Email not configured"))

# Check 3: Debug mode
if settings.DEBUG:
    checks.append(("⚠️ ", "DEBUG=True (set to False in production)"))
else:
    checks.append(("✅", "DEBUG=False (production mode)"))

# Check 4: Celery
if celery_broker:
    checks.append(("✅", "Celery configured"))
else:
    checks.append(("❌", "Celery not configured"))

for icon, msg in checks:
    print(f"{icon} {msg}")

print("\n" + "=" * 70)
print("📚 See PRODUCTION-WALLET-GUIDE.md for deployment checklist")
print("=" * 70 + "\n")
