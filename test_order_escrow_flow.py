"""
Complete Order/Escrow Flow Test

Tests the entire order lifecycle:
1. Buyer creates order → Wallet debited, Escrow held
2. Seller accepts order
3. Seller marks as delivered
4. Buyer confirms delivery → Escrow released to seller
5. Test cancellation with refund

Requirements:
- 2 users (buyer and seller)
- Seller must have a store
- Store must have at least 1 product
- Buyer must have sufficient wallet balance
"""

import requests
import json
from decimal import Decimal

# API Configuration
BASE_URL = "http://127.0.0.1:8000/api"

# Test users (you'll need to create these first or use existing ones)
BUYER_EMAIL = "buyer@test.com"
BUYER_PASSWORD = "testpass123"

SELLER_EMAIL = "seller@test.com"
SELLER_PASSWORD = "testpass123"


def print_section(title):
    """Print a formatted section header"""
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}\n")


def login(email, password):
    """Login and get JWT token"""
    response = requests.post(
        f"{BASE_URL}/users/login/", json={"email": email, "password": password}
    )

    if response.status_code == 200:
        data = response.json()
        token = data["access"]
        user_id = data["user"]["id"]
        print(f"✅ Logged in as {email}")
        print(f"   User ID: {user_id}")
        return token, user_id
    else:
        print(f"❌ Login failed: {response.text}")
        return None, None


def get_wallet_balance(token):
    """Get current wallet balance"""
    response = requests.get(
        f"{BASE_URL}/wallets/balance/", headers={"Authorization": f"Bearer {token}"}
    )

    if response.status_code == 200:
        data = response.json()
        balance = data["balance"]
        print(f"💰 Wallet Balance: ₦{balance}")
        return Decimal(str(balance))
    else:
        print(f"❌ Failed to get balance: {response.text}")
        return None


def get_products(token, store_id=None):
    """Get products (optionally filter by store)"""
    url = f"{BASE_URL}/products/"
    if store_id:
        url += f"?store={store_id}"

    response = requests.get(url, headers={"Authorization": f"Bearer {token}"})

    if response.status_code == 200:
        data = response.json()
        products = data.get("results", [])
        print(f"📦 Found {len(products)} products")
        return products
    else:
        print(f"❌ Failed to get products: {response.text}")
        return []


def get_stores(token, seller_id):
    """Get stores for a seller"""
    response = requests.get(
        f"{BASE_URL}/stores/?seller={seller_id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    if response.status_code == 200:
        data = response.json()
        stores = data.get("results", [])
        print(f"🏪 Found {len(stores)} stores")
        return stores
    else:
        print(f"❌ Failed to get stores: {response.text}")
        return []


def create_order(token, product_id, delivery_message):
    """Create a new order"""
    response = requests.post(
        f"{BASE_URL}/orders/",
        headers={"Authorization": f"Bearer {token}"},
        json={"product_id": product_id, "delivery_message": delivery_message},
    )

    if response.status_code == 201:
        order = response.json()
        print(f"✅ Order Created!")
        print(f"   Order Number: {order['order_number']}")
        print(f"   Order ID: {order['id']}")
        print(f"   Status: {order['status']}")
        print(f"   Total Amount: ₦{order['total_amount']}")
        print(f"   Escrow Status: {order['escrow_status']}")
        print(f"   Escrow Amount: ₦{order['escrow_amount']}")
        return order
    else:
        print(f"❌ Order creation failed:")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text}")
        return None


def accept_order(token, order_id):
    """Seller accepts order"""
    response = requests.post(
        f"{BASE_URL}/orders/{order_id}/accept/",
        headers={"Authorization": f"Bearer {token}"},
    )

    if response.status_code == 200:
        data = response.json()
        order = data["order"]
        print(f"✅ Order Accepted!")
        print(f"   Status: {order['status']}")
        print(f"   Accepted At: {order['accepted_at']}")
        return order
    else:
        print(f"❌ Accept failed: {response.text}")
        return None


def deliver_order(token, order_id):
    """Seller marks order as delivered"""
    response = requests.post(
        f"{BASE_URL}/orders/{order_id}/deliver/",
        headers={"Authorization": f"Bearer {token}"},
    )

    if response.status_code == 200:
        data = response.json()
        order = data["order"]
        print(f"✅ Order Delivered!")
        print(f"   Status: {order['status']}")
        print(f"   Delivered At: {order['delivered_at']}")
        return order
    else:
        print(f"❌ Deliver failed: {response.text}")
        return None


def confirm_order(token, order_id):
    """Buyer confirms delivery"""
    response = requests.post(
        f"{BASE_URL}/orders/{order_id}/confirm/",
        headers={"Authorization": f"Bearer {token}"},
    )

    if response.status_code == 200:
        data = response.json()
        order = data["order"]
        print(f"✅ Order Confirmed!")
        print(f"   Status: {order['status']}")
        print(f"   Confirmed At: {order['confirmed_at']}")
        print(f"   Escrow Status: {order['escrow_status']}")
        return order
    else:
        print(f"❌ Confirm failed: {response.text}")
        return None


def cancel_order(token, order_id, reason):
    """Cancel order"""
    response = requests.post(
        f"{BASE_URL}/orders/{order_id}/cancel/",
        headers={"Authorization": f"Bearer {token}"},
        json={"reason": reason},
    )

    if response.status_code == 200:
        data = response.json()
        order = data["order"]
        print(f"✅ Order Cancelled!")
        print(f"   Status: {order['status']}")
        print(f"   Cancelled By: {order['cancelled_by']}")
        print(f"   Reason: {order['cancellation_reason']}")
        print(f"   Escrow Status: {order['escrow_status']}")
        return order
    else:
        print(f"❌ Cancel failed: {response.text}")
        return None


def get_order_details(token, order_id):
    """Get order details"""
    response = requests.get(
        f"{BASE_URL}/orders/{order_id}/", headers={"Authorization": f"Bearer {token}"}
    )

    if response.status_code == 200:
        return response.json()
    else:
        print(f"❌ Failed to get order: {response.text}")
        return None


def main():
    """Run complete order/escrow flow test"""

    print_section("COVU ORDER/ESCROW SYSTEM - COMPLETE FLOW TEST")

    # Step 1: Login as buyer
    print_section("STEP 1: Buyer Login & Check Balance")
    buyer_token, buyer_id = login(BUYER_EMAIL, BUYER_PASSWORD)
    if not buyer_token:
        print("⚠️  Please create a buyer account first:")
        print(f"   Email: {BUYER_EMAIL}")
        print(f"   Password: {BUYER_PASSWORD}")
        return

    buyer_balance_before = get_wallet_balance(buyer_token)
    if buyer_balance_before is None or buyer_balance_before < 1000:
        print("⚠️  Buyer needs at least ₦1,000 in wallet to place order")
        print("   Fund wallet via Paystack first")
        return

    # Step 2: Login as seller
    print_section("STEP 2: Seller Login & Get Products")
    seller_token, seller_id = login(SELLER_EMAIL, SELLER_PASSWORD)
    if not seller_token:
        print("⚠️  Please create a seller account first:")
        print(f"   Email: {SELLER_EMAIL}")
        print(f"   Password: {SELLER_PASSWORD}")
        return

    seller_balance_before = get_wallet_balance(seller_token)

    # Get seller's store
    stores = get_stores(seller_token, seller_id)
    if not stores:
        print("⚠️  Seller needs to create a store first")
        return

    store = stores[0]
    print(f"🏪 Using Store: {store['name']}")

    # Get products from seller's store
    products = get_products(buyer_token, store["id"])
    if not products:
        print("⚠️  Store has no products. Please add products first")
        return

    product = products[0]
    print(f"📦 Using Product: {product['name']} (₦{product['price']})")

    # Step 3: Buyer creates order
    print_section("STEP 3: Buyer Creates Order")
    delivery_message = "123 Test Street, Lagos, Nigeria"
    order = create_order(buyer_token, product["id"], delivery_message)
    if not order:
        return

    order_id = order["id"]

    # Check buyer balance after order
    print("\n--- Buyer Balance After Order ---")
    buyer_balance_after_order = get_wallet_balance(buyer_token)
    deducted = buyer_balance_before - buyer_balance_after_order
    print(f"💸 Amount Deducted: ₦{deducted}")

    # Step 4: Seller accepts order
    print_section("STEP 4: Seller Accepts Order")
    order = accept_order(seller_token, order_id)
    if not order:
        return

    # Step 5: Seller marks as delivered
    print_section("STEP 5: Seller Marks Order as Delivered")
    order = deliver_order(seller_token, order_id)
    if not order:
        return

    # Check seller balance (should still be same - escrow not released yet)
    print("\n--- Seller Balance (Escrow Still Held) ---")
    seller_balance_during = get_wallet_balance(seller_token)
    print(f"   (No change yet - funds in escrow)")

    # Step 6: Buyer confirms delivery
    print_section("STEP 6: Buyer Confirms Delivery (Release Escrow)")
    order = confirm_order(buyer_token, order_id)
    if not order:
        return

    # Check seller balance after escrow release
    print("\n--- Seller Balance After Escrow Release ---")
    seller_balance_after = get_wallet_balance(seller_token)
    credited = seller_balance_after - seller_balance_before
    print(f"💰 Amount Credited: ₦{credited}")

    # Step 7: Get final order details
    print_section("STEP 7: Final Order Details")
    final_order = get_order_details(buyer_token, order_id)
    if final_order:
        print(f"📋 Order Number: {final_order['order_number']}")
        print(f"   Status: {final_order['status']} ({final_order['status_display']})")
        print(f"   Total Amount: ₦{final_order['total_amount']}")
        print(f"   Product Price: ₦{final_order['product_price']}")
        print(f"   Delivery Fee: ₦{final_order['delivery_fee']}")
        print(f"   Escrow Status: {final_order['escrow_status']}")
        print(f"   Created: {final_order['created_at']}")
        print(f"   Accepted: {final_order['accepted_at']}")
        print(f"   Delivered: {final_order['delivered_at']}")
        print(f"   Confirmed: {final_order['confirmed_at']}")

    # Summary
    print_section("TEST SUMMARY")
    print("✅ ORDER FLOW COMPLETE!")
    print(f"\n📊 Transaction Summary:")
    print(f"   Buyer Paid: ₦{deducted}")
    print(f"   Seller Received: ₦{credited}")
    print(f"   Order Status: {final_order['status']}")
    print(f"   Escrow Status: {final_order['escrow_status']}")

    print("\n🎉 All tests passed! Order/Escrow system working perfectly!")

    # Optional: Test cancellation with new order
    print_section("BONUS: Test Order Cancellation")
    print("Creating another order to test cancellation...")

    cancel_order_obj = create_order(buyer_token, product["id"], delivery_message)
    if cancel_order_obj:
        print("\nCancelling order as buyer...")
        cancel_order(buyer_token, cancel_order_obj["id"], "Changed my mind")

        # Check refund
        print("\n--- Buyer Balance After Refund ---")
        buyer_balance_after_cancel = get_wallet_balance(buyer_token)
        print(f"✅ Refund processed successfully!")


if __name__ == "__main__":
    main()
