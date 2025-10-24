# 📊 Frontend Order Flow Analysis

## Current Implementation Status

**Date:** October 23, 2025  
**Analysis:** Complete Frontend Order System (localStorage-based)

---

## 🔍 Current Order Flow (Frontend Only)

### **Order Creation Flow**

```
Product Detail Page → Buy Now → Purchase Page → Process Order → Orders Page
```

### **Detailed Flow Breakdown:**

#### **1. Product Selection (product-detail.js)**

```javascript
// Line 301-312: Buy Now button
setupBuyNowButton() {
    buyNowBtn.addEventListener('click', () => {
        // Store product in localStorage
        localStorage.setItem('purchaseProduct', JSON.stringify(currentProduct));

        // Navigate to orders page (NOT purchase page!)
        window.location.href = 'orders.html';
    });
}
```

**Issue Found:**

- ❌ Button navigates to `orders.html` instead of `purchase.html`
- ❌ Uses `purchaseProduct` key but purchase.js expects `selectedProduct`

---

#### **2. Purchase Page (purchase.html + purchase.js)**

**Features Implemented:**

- ✅ Product information display
- ✅ Wallet balance check
- ✅ Payment amount input
- ✅ Delivery fee calculation (fixed ₦500)
- ✅ Paystack integration for wallet top-up
- ✅ Order creation with localStorage
- ✅ Purchase confirmation modal with loading/success states

**Current Behavior:**

```javascript
// Lines 46-59: Load product data
loadProductData() {
    // Gets 'selectedProduct' from localStorage
    const productData = JSON.parse(localStorage.getItem('selectedProduct') || '{}');

    // Calculate totals
    const subtotal = productData.price || 0;
    const deliveryFee = 500; // Fixed
    const total = subtotal + deliveryFee;
}

// Lines 113-129: Create order
createOrder(productData, totalAmount) {
    const newOrder = {
        id: generateOrderId(),  // ORD-001, ORD-002, etc.
        productName: productData.name,
        productImage: productData.image,
        storeName: productData.store,
        price: productData.price,
        quantity: 1,
        status: 'pending',  // waiting for seller confirmation
        orderDate: new Date().toISOString(),
        total: totalAmount
    };

    // Store in localStorage
    orders.push(newOrder);
    localStorage.setItem('orders', JSON.stringify(orders));

    return newOrder.id;
}

// Lines 217-236: Process purchase
processPurchase(paymentAmount, productData) {
    // 1. Debit wallet
    const newBalance = currentBalance - paymentAmount;
    localStorage.setItem('walletBalance', newBalance.toString());

    // 2. Create order
    const orderId = createOrder(productData, paymentAmount);

    // 3. Show success modal
    // 4. Clear selectedProduct
    // 5. Redirect to orders page after confirmation
}
```

---

#### **3. Orders Page (orders.js)**

**Current Order Statuses:**

- `pending` - Waiting for seller confirmation
- `confirmed` - Order confirmed, delivery in progress
- `delivered` - Order has been delivered
- `cancelled` - Order cancelled

**Status Actions (Buyer View):**

```javascript
// Lines 134-161: Status mapping
getStatusInfo(status) {
    'pending': {
        text: 'Pending',
        description: 'Order added, waiting for seller confirmation',
        button: { text: 'Cancel Order', action: 'cancel' }
    },
    'confirmed': {
        text: 'Confirmed',
        description: 'Order confirmed, delivery in progress',
        button: { text: 'Mark as Delivered', action: 'deliver' }
    },
    'delivered': {
        text: 'Delivered',
        description: 'Order has been delivered successfully',
        button: null
    },
    'cancelled': {
        text: 'Cancelled',
        description: 'Order has been cancelled',
        button: null
    }
}

// Lines 173-196: Handle actions
handleOrderAction(orderId, action) {
    if (action === 'cancel') {
        // Change status to 'cancelled'
        // No wallet refund implemented!
    } else if (action === 'deliver') {
        // Change status to 'delivered'
        // This seems wrong - buyer shouldn't mark as delivered
    }
}
```

**Issues Found:**

- ❌ No wallet refund on cancellation
- ❌ Buyer can "Mark as Delivered" (should be seller action)
- ❌ No seller view/acceptance flow
- ❌ Missing "Confirm Receipt" action for buyers
- ❌ No escrow concept

---

## 🎯 Backend API Comparison

### **Backend Order Statuses:**

```
PENDING → ACCEPTED → DELIVERED → CONFIRMED (or CANCELLED)
```

### **Backend Order Actions:**

| Action          | Who          | From Status            | To Status | Escrow   |
| --------------- | ------------ | ---------------------- | --------- | -------- |
| Create Order    | Buyer        | -                      | PENDING   | HELD     |
| Accept Order    | Seller       | PENDING                | ACCEPTED  | HELD     |
| Mark Delivered  | Seller       | ACCEPTED               | DELIVERED | HELD     |
| Confirm Receipt | Buyer        | DELIVERED              | CONFIRMED | RELEASED |
| Cancel Order    | Buyer/Seller | Any (before CONFIRMED) | CANCELLED | REFUNDED |

### **Backend Order Model:**

```python
{
    "id": "uuid",
    "order_number": "A1B2C3D4",
    "buyer": {...},
    "seller": {...},
    "product": {...},
    "quantity": 1,
    "product_price": "15000.00",
    "delivery_fee": "500.00",
    "total_amount": "15500.00",
    "status": "PENDING",
    "delivery_address": "123 Main Street",
    "escrow_status": "HELD",
    "escrow_amount": 15500.00,
    "created_at": "2025-10-21T10:30:00Z",
    "accepted_at": null,
    "delivered_at": null,
    "confirmed_at": null,
    "cancelled_at": null,
    "cancelled_by": null,
    "cancellation_reason": null
}
```

---

## 🔄 Required Changes for Backend Integration

### **Phase 3A: Order Creation**

#### **1. Fix Product Detail → Purchase Navigation**

**File:** `product-detail.js`

**Current (Line 309):**

```javascript
window.location.href = "orders.html";
```

**Change to:**

```javascript
window.location.href = "purchase.html";
```

**Also fix localStorage key (Line 307):**

```javascript
// Current:
localStorage.setItem("purchaseProduct", JSON.stringify(currentProduct));

// Change to:
localStorage.setItem("selectedProduct", JSON.stringify(currentProduct));
```

---

#### **2. Update Purchase Page for Backend API**

**File:** `purchase.js`

**Add delivery address input** (missing in current HTML):

```html
<!-- Add to purchase.html after payment amount -->
<div class="mt-6">
  <label
    for="deliveryAddress"
    class="block text-sm font-medium text-gray-700 mb-2"
  >
    Delivery Address *
  </label>
  <textarea
    id="deliveryAddress"
    rows="3"
    class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:border-primary-orange"
    placeholder="Enter your delivery address"
    required
  ></textarea>
</div>
```

**Update processPurchase() function:**

```javascript
async function processPurchase(paymentAmount, productData) {
  try {
    // Get delivery address
    const deliveryAddress = document
      .getElementById("deliveryAddress")
      .value.trim();

    if (!deliveryAddress) {
      alert("Please enter a delivery address");
      return;
    }

    // Call backend API
    const response = await api.post(API_CONFIG.ENDPOINTS.ORDERS, {
      product_id: productData.id,
      delivery_address: deliveryAddress,
    });

    // Update wallet balance from response
    const currentUser = api.getCurrentUser();
    currentUser.wallet_balance =
      parseFloat(currentUser.wallet_balance) -
      parseFloat(response.total_amount);
    api.setCurrentUser(currentUser);

    // Update UI
    document.getElementById("walletBalance").textContent = formatCurrency(
      currentUser.wallet_balance
    );

    // Show success with real order ID
    orderIdElement.textContent = response.order_number;

    // Clear selected product
    localStorage.removeItem("selectedProduct");

    // Show success message
    showToast("Order created successfully! Funds held in escrow.");
  } catch (error) {
    console.error("Order creation error:", error);

    let errorMessage = "Failed to create order. Please try again.";

    if (error.message && error.message.includes("Insufficient funds")) {
      errorMessage = "Insufficient wallet balance. Please top up.";
    } else if (error.message) {
      errorMessage = error.message;
    }

    alert(errorMessage);
  }
}
```

---

### **Phase 3B: Order Management**

#### **3. Update orders.js for Backend Integration**

**Add at top of file:**

```javascript
document.addEventListener("DOMContentLoaded", async function () {
  // Check authentication
  if (!api.isAuthenticated()) {
    window.location.href = "login.html";
    return;
  }

  lucide.createIcons();

  // Load orders from backend
  await loadOrders();
});
```

**Replace loadOrders() function:**

```javascript
async function loadOrders() {
  const container = document.getElementById("ordersContainer");
  const emptyState = document.getElementById("emptyState");

  try {
    // Show loading
    container.innerHTML =
      '<div class="text-center py-12">Loading orders...</div>';

    // Fetch from backend
    const response = await api.get(API_CONFIG.ENDPOINTS.ORDERS);

    const orders = response.results || [];

    if (orders.length === 0) {
      container.innerHTML = "";
      emptyState.classList.remove("hidden");
      return;
    }

    displayOrders(orders);
  } catch (error) {
    console.error("Error loading orders:", error);
    container.innerHTML = `
            <div class="text-center py-12">
                <p class="text-red-500 mb-4">Failed to load orders</p>
                <button onclick="loadOrders()" class="bg-primary-orange text-white px-6 py-2 rounded-lg">
                    Retry
                </button>
            </div>
        `;
  }
}
```

**Update createOrderCard() for backend format:**

```javascript
function createOrderCard(order) {
  const card = document.createElement("div");
  card.className = "bg-white rounded-lg shadow-sm p-4";

  const statusInfo = getStatusInfo(order.status);
  const orderDate = formatDate(order.created_at);

  // Backend uses order.product object
  const productName = order.product.name;
  const productImage = order.product.images || "placeholder.jpg";
  const storeName = order.product.store_name;

  card.innerHTML = `
        <div class="flex items-center gap-4 mb-4">
            <img src="${productImage}" alt="${productName}" class="w-16 h-16 object-cover rounded-lg">
            <div class="flex-1">
                <h3 class="font-semibold text-gray-800 mb-1">${productName}</h3>
                <p class="text-sm text-gray-500 mb-1">${storeName}</p>
                <div class="flex items-center justify-between">
                    <span class="text-primary-orange font-bold">₦${parseFloat(
                      order.total_amount
                    ).toLocaleString()}</span>
                    <span class="status-badge ${statusInfo.class}">${
    statusInfo.text
  }</span>
                </div>
            </div>
        </div>

        <div class="flex items-center justify-between text-sm text-gray-500 mb-4">
            <span>Order #${order.order_number}</span>
            <span>${orderDate}</span>
        </div>

        <div class="flex items-center justify-between">
            <div class="text-sm text-gray-600">
                ${statusInfo.description}
            </div>
            ${
              statusInfo.button
                ? createActionButton(order, statusInfo.button)
                : ""
            }
        </div>
    `;

  return card;
}
```

**Update getStatusInfo() for backend statuses:**

```javascript
function getStatusInfo(status) {
  const statusMap = {
    PENDING: {
      text: "Pending",
      class: "status-pending",
      description: "Waiting for seller confirmation",
      button: {
        text: "Cancel Order",
        action: "cancel",
        class: "bg-red-500 hover:bg-red-600",
      },
    },
    ACCEPTED: {
      text: "Accepted",
      class: "status-confirmed",
      description: "Seller confirmed, preparing delivery",
      button: null,
    },
    DELIVERED: {
      text: "Delivered",
      class: "status-delivered",
      description: "Awaiting your confirmation",
      button: {
        text: "Confirm Receipt",
        action: "confirm",
        class: "bg-primary-green hover:bg-green-600",
      },
    },
    CONFIRMED: {
      text: "Completed",
      class: "status-delivered",
      description: "Order completed successfully",
      button: null,
    },
    CANCELLED: {
      text: "Cancelled",
      class: "status-cancelled",
      description: "Order has been cancelled",
      button: null,
    },
  };

  return statusMap[status] || statusMap["PENDING"];
}
```

**Update handleOrderAction() for backend API:**

```javascript
async function handleOrderAction(orderId, action) {
  const confirmMsg =
    action === "cancel"
      ? "Are you sure you want to cancel this order? Your wallet will be refunded."
      : "Confirm that you have received this order? Payment will be released to seller.";

  if (!confirm(confirmMsg)) return;

  try {
    let endpoint;

    if (action === "cancel") {
      endpoint = API_CONFIG.ENDPOINTS.ORDER_CANCEL(orderId);
    } else if (action === "confirm") {
      endpoint = API_CONFIG.ENDPOINTS.ORDER_CONFIRM(orderId);
    }

    // Call API
    const response = await api.post(endpoint, {
      reason: action === "cancel" ? "Changed my mind" : undefined,
    });

    // Show success message
    showMessage(response.message || "Order updated successfully", "success");

    // Reload orders
    await loadOrders();
  } catch (error) {
    console.error("Order action error:", error);
    showMessage(error.message || "Action failed", "error");
  }
}
```

---

## 📝 Summary of Changes Needed

### **Critical Fixes:**

1. ✅ **product-detail.js (Line 309):** Change redirect from `orders.html` to `purchase.html`
2. ✅ **product-detail.js (Line 307):** Change localStorage key from `purchaseProduct` to `selectedProduct`
3. ✅ **purchase.html:** Add delivery address textarea input
4. ✅ **purchase.js:** Replace `processPurchase()` with backend API call
5. ✅ **orders.js:** Replace `loadOrders()` with backend API call
6. ✅ **orders.js:** Update `createOrderCard()` for backend response format
7. ✅ **orders.js:** Update `getStatusInfo()` for backend statuses (PENDING, ACCEPTED, DELIVERED, CONFIRMED, CANCELLED)
8. ✅ **orders.js:** Update `handleOrderAction()` with backend API calls

### **Optional Enhancements:**

9. ⏳ Add seller view tab to orders page (switch between buyer/seller views)
10. ⏳ Add order details modal/page
11. ⏳ Add real-time order status updates
12. ⏳ Add order tracking/timeline
13. ⏳ Add delivery fee calculation based on buyer location

---

## 🎯 Implementation Priority

### **Step 1: Fix Order Creation Flow**

- Fix product-detail.js navigation
- Add delivery address input to purchase.html
- Update purchase.js to call backend API
- Test: Create order → Check wallet debited → Check escrow held

### **Step 2: Fix Order Management**

- Update orders.js to fetch from backend
- Update order card for backend format
- Update status info for backend statuses
- Test: View orders → Cancel order → Confirm receipt

### **Step 3: Testing**

- End-to-end buyer flow
- End-to-end seller flow (if implemented)
- Cancellation and refunds
- Edge cases (insufficient funds, etc.)

---

## 🚀 Ready to Implement!

All analysis complete. Current frontend has a solid foundation but needs:

- Backend API integration
- Status mapping updates
- Escrow concept integration
- Delivery address collection

Let's proceed with implementation! 🎉
