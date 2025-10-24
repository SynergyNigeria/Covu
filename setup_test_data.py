"""
Setup test data for Order/Escrow system testing

Creates:
1. Buyer user with funded wallet
2. Seller user with store and product
"""

import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "covu.settings")
django.setup()

from django.contrib.auth import get_user_model
from stores.models import Store
from products.models import Product
from wallets.models import Wallet, WalletTransaction
from decimal import Decimal
from django.db import transaction

User = get_user_model()

print("=" * 80)
print("  SETTING UP TEST DATA FOR ORDER/ESCROW SYSTEM")
print("=" * 80)

# Test user credentials
BUYER_EMAIL = "buyer@test.com"
BUYER_PASSWORD = "testpass123"
BUYER_FULL_NAME = "Test Buyer"

SELLER_EMAIL = "seller@test.com"
SELLER_PASSWORD = "testpass123"
SELLER_FULL_NAME = "Test Seller"

INITIAL_WALLET_BALANCE = Decimal("10000.00")  # ₦10,000

try:
    with transaction.atomic():

        # ===========================================
        # STEP 1: CREATE OR GET BUYER
        # ===========================================
        print("\n1. SETTING UP BUYER...")

        buyer, created = User.objects.get_or_create(
            email=BUYER_EMAIL,
            defaults={
                "full_name": BUYER_FULL_NAME,
                "phone_number": "08012345678",
                "state": "lagos",
                "city": "Ikeja",
                "is_active": True,
            },
        )

        if created:
            buyer.set_password(BUYER_PASSWORD)
            buyer.save()
            print(f"   ✅ Created buyer: {BUYER_EMAIL}")
        else:
            print(f"   ℹ️  Buyer already exists: {BUYER_EMAIL}")

        # Fund buyer wallet if needed
        buyer_wallet = Wallet.objects.get(user=buyer)
        current_balance = buyer_wallet.balance

        if current_balance < INITIAL_WALLET_BALANCE:
            amount_to_add = INITIAL_WALLET_BALANCE - current_balance

            WalletTransaction.objects.create(
                wallet=buyer_wallet,
                transaction_type="CREDIT",
                amount=amount_to_add,
                reference=f"TEST_FUND_{buyer.id}",
                description="Test wallet funding",
                balance_before=current_balance,
                balance_after=INITIAL_WALLET_BALANCE,
                metadata={"test_data": True},
            )

            print(
                f"   💰 Funded buyer wallet: ₦{current_balance:.2f} → ₦{INITIAL_WALLET_BALANCE:.2f}"
            )
        else:
            print(f"   💰 Buyer wallet balance: ₦{current_balance:.2f}")

        # ===========================================
        # STEP 2: CREATE OR GET SELLER
        # ===========================================
        print("\n2. SETTING UP SELLER...")

        seller, created = User.objects.get_or_create(
            email=SELLER_EMAIL,
            defaults={
                "full_name": SELLER_FULL_NAME,
                "phone_number": "08087654321",
                "state": "lagos",
                "city": "Surulere",
                "is_active": True,
            },
        )

        if created:
            seller.set_password(SELLER_PASSWORD)
            seller.save()
            print(f"   ✅ Created seller: {SELLER_EMAIL}")
        else:
            print(f"   ℹ️  Seller already exists: {SELLER_EMAIL}")

        seller_wallet = Wallet.objects.get(user=seller)
        print(f"   💰 Seller wallet balance: ₦{seller_wallet.balance:.2f}")

        # ===========================================
        # STEP 3: CREATE OR GET STORE
        # ===========================================
        print("\n3. SETTING UP STORE...")

        store, created = Store.objects.get_or_create(
            seller=seller,
            defaults={
                "name": "Test Fashion Store",
                "description": "A test store for Order/Escrow system testing",
                "state": "lagos",
                "city": "Surulere",
                "delivery_within_lga": Decimal("500.00"),
                "delivery_outside_lga": Decimal("1500.00"),
                "is_active": True,
            },
        )

        if created:
            print(f"   ✅ Created store: {store.name}")
        else:
            print(f"   ℹ️  Store already exists: {store.name}")

        print(f"      Delivery (within LGA): ₦{store.delivery_within_lga:.2f}")
        print(f"      Delivery (outside LGA): ₦{store.delivery_outside_lga:.2f}")

        # ===========================================
        # STEP 4: CREATE TEST PRODUCTS
        # ===========================================
        print("\n4. SETTING UP PRODUCTS...")

        products_data = [
            {
                "name": "Test Designer Dress",
                "description": "Beautiful designer dress for testing",
                "price": Decimal("2500.00"),
                "category": "LADIES_CLOTHES",
            },
            {
                "name": "Test Sneakers",
                "description": "Comfortable sneakers for testing",
                "price": Decimal("1500.00"),
                "category": "ACCESSORIES",
            },
            {
                "name": "Test Handbag",
                "description": "Stylish handbag for testing",
                "price": Decimal("3000.00"),
                "category": "BAGS",
            },
        ]

        created_products = []
        for product_data in products_data:
            product, created = Product.objects.get_or_create(
                store=store,
                name=product_data["name"],
                defaults={
                    "description": product_data["description"],
                    "price": product_data["price"],
                    "category": product_data["category"],
                    "is_active": True,
                },
            )

            if created:
                print(f"   ✅ Created product: {product.name} (₦{product.price:.2f})")
            else:
                print(f"   ℹ️  Product exists: {product.name} (₦{product.price:.2f})")

            created_products.append(product)

        # ===========================================
        # SUMMARY
        # ===========================================
        print("\n" + "=" * 80)
        print("  SETUP COMPLETE!")
        print("=" * 80)

        print("\n📋 TEST DATA SUMMARY:")
        print(f"\n👤 BUYER:")
        print(f"   Email: {buyer.email}")
        print(f"   Password: {BUYER_PASSWORD}")
        print(f"   Wallet Balance: ₦{buyer_wallet.balance:.2f}")
        print(f"   Location: {buyer.city}, {buyer.state}")

        print(f"\n👤 SELLER:")
        print(f"   Email: {seller.email}")
        print(f"   Password: {SELLER_PASSWORD}")
        print(f"   Wallet Balance: ₦{seller_wallet.balance:.2f}")
        print(f"   Location: {seller.city}, {seller.state}")

        print(f"\n🏪 STORE:")
        print(f"   Name: {store.name}")
        print(f"   ID: {store.id}")
        print(f"   Delivery (same city): ₦{store.delivery_within_lga:.2f}")
        print(f"   Delivery (different city): ₦{store.delivery_outside_lga:.2f}")

        print(f"\n📦 PRODUCTS:")
        for product in created_products:
            print(f"   • {product.name} - ₦{product.price:.2f} ({product.category})")
            print(f"     ID: {product.id}")

        print("\n" + "=" * 80)
        print("✅ Ready to test Order/Escrow system!")
        print("\nNext: Run 'python test_order_escrow_flow.py'")
        print("=" * 80)

except Exception as e:
    print(f"\n❌ ERROR: {str(e)}")
    import traceback

    traceback.print_exc()
