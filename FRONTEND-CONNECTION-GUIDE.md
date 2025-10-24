# 🚀 Frontend Connection Quick Start

## ✅ What's Ready

1. **✅ Backend API** - All Order/Escrow endpoints ready
2. **✅ Test Data** - Buyer & seller accounts with test products
3. **✅ Documentation** - Complete API guide in `FRONTEND-API-GUIDE.md`
4. **✅ API Tester** - Interactive tester in `api-tester.html`
5. **✅ CORS** - Configured for `localhost:5500` and `localhost:3000`

---

## 🎯 Quick Start (3 Steps)

### Step 1: Start Backend Server

```bash
# Make sure you're in the Backend directory
cd C:\Users\DELL\Desktop\Backend

# Activate virtual environment (if not already active)
.\venv\Scripts\activate

# Start Django server
python manage.py runserver
```

**Backend will run on:** `http://localhost:8000`

### Step 2: Test Connection

**Option A: Use API Tester (Recommended)**

1. Open `api-tester.html` in your browser (double-click it)
2. Click "Test Connection" button
3. Login with test credentials:
   - Email: `buyer@test.com`
   - Password: `testpass123`
4. Test all endpoints interactively!

**Option B: Test with cURL**

```bash
# Test if backend is accessible
curl http://localhost:8000/api/stores/

# Login
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"buyer@test.com","password":"testpass123"}'
```

### Step 3: Connect Your Frontend

**JavaScript Example:**

```javascript
const API_BASE = "http://localhost:8000/api";

// Test connection
fetch(`${API_BASE}/stores/`)
  .then((res) => res.json())
  .then((data) => console.log("✅ Backend connected!", data))
  .catch((err) => console.error("❌ Connection failed:", err));

// Login
async function login(email, password) {
  const response = await fetch(`${API_BASE}/auth/login/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });

  const data = await response.json();

  if (response.ok) {
    // Save token for future requests
    localStorage.setItem("token", data.access);
    console.log("✅ Logged in!", data.user);
    return data;
  } else {
    console.error("❌ Login failed:", data);
    throw new Error(data.error);
  }
}

// Create order
async function createOrder(productId, deliveryAddress) {
  const token = localStorage.getItem("token");

  const response = await fetch(`${API_BASE}/orders/`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      product_id: productId,
      delivery_address: deliveryAddress,
    }),
  });

  const data = await response.json();

  if (response.ok) {
    console.log("✅ Order created!", data);
    return data;
  } else {
    console.error("❌ Order failed:", data);
    throw new Error(data.error);
  }
}
```

---

## 📚 API Documentation

See **`FRONTEND-API-GUIDE.md`** for:

- Complete API endpoint list
- Request/response examples
- Error handling
- Complete order flow walkthrough
- Authentication guide

---

## 🧪 Test Accounts

### Buyer Account

- **Email:** `buyer@test.com`
- **Password:** `testpass123`
- **Wallet Balance:** ₦10,000
- **Location:** Ikeja, Lagos

### Seller Account

- **Email:** `seller@test.com`
- **Password:** `testpass123`
- **Store:** Test Fashion Store
- **Products:** 3 items (₦1500-₦3000)

---

## 🔧 Troubleshooting

### ❌ CORS Error

**Problem:** Browser console shows CORS error

**Solution 1:** Check `.env` file has your frontend URL:

```env
CORS_ALLOWED_ORIGINS=http://localhost:5500,http://localhost:3000
```

**Solution 2:** Restart Django server after changing `.env`

### ❌ Connection Refused

**Problem:** Cannot connect to `localhost:8000`

**Solution:** Make sure Django server is running:

```bash
python manage.py runserver
```

### ❌ 401 Unauthorized

**Problem:** API returns 401 error

**Solution:** Include JWT token in request header:

```javascript
headers: {
  'Authorization': `Bearer ${token}`
}
```

### ❌ 400 Bad Request

**Problem:** Order creation fails

**Possible Causes:**

1. **Insufficient funds** - Check wallet balance
2. **Buying from own store** - Buyer can't buy from their own store
3. **Invalid product ID** - Product must exist and be active
4. **Missing delivery address** - Required field

---

## 📊 Complete Order Flow (Frontend Implementation)

### 1. User Registration/Login

```javascript
// Register new user
POST /
  api /
  auth /
  register /
  {
    email: "newuser@example.com",
    password: "SecurePass123!",
    password_confirm: "SecurePass123!",
    full_name: "New User",
    phone_number: "08012345678",
    state: "lagos",
    city: "Ikeja",
  };

// Login
POST /
  api /
  auth /
  login /
  {
    email: "buyer@test.com",
    password: "testpass123",
  };
// Returns: { access, refresh, user }
```

### 2. Browse Products

```javascript
// List all products
GET /api/products/

// Filter by category
GET /api/products/?category=LADIES_CLOTHES

// Search
GET /api/products/?search=dress

// Filter by store
GET /api/products/?store={store_id}
```

### 3. Check Wallet Balance

```javascript
GET /api/wallet/balance/
Authorization: Bearer <token>

// Returns: { balance: "10000.00", wallet_id: "uuid" }
```

### 4. Create Order

```javascript
POST /api/orders/
Authorization: Bearer <token>
{
  "product_id": "uuid",
  "delivery_address": "123 Main Street, Lagos"
}

// What happens:
// 1. ✅ Buyer's wallet debited
// 2. ✅ Money held in escrow
// 3. ✅ Order status: PENDING
// 4. ✅ Seller notified via email
```

### 5. Seller Accepts Order

```javascript
POST /api/orders/{order_id}/accept/
Authorization: Bearer <seller_token>

// Order status: PENDING → ACCEPTED
// Buyer gets email notification
```

### 6. Seller Marks as Delivered

```javascript
POST /api/orders/{order_id}/deliver/
Authorization: Bearer <seller_token>

// Order status: ACCEPTED → DELIVERED
// Buyer gets email notification
```

### 7. Buyer Confirms Delivery

```javascript
POST /api/orders/{order_id}/confirm/
Authorization: Bearer <buyer_token>

// Order status: DELIVERED → CONFIRMED
// Escrow released: HELD → RELEASED
// Seller's wallet credited
// Seller gets email notification
// 🎉 Transaction complete!
```

### 8. (Optional) Cancel Order

```javascript
POST /api/orders/{order_id}/cancel/
Authorization: Bearer <token>
{
  "reason": "Changed my mind"
}

// Order status → CANCELLED
// Escrow refunded: HELD → REFUNDED
// Buyer's wallet refunded
// Both parties notified
```

---

## 🎨 Frontend UI Suggestions

### Order Status Badge Colors

```css
.status-pending {
  background: #ffc107;
} /* Orange */
.status-accepted {
  background: #2196f3;
} /* Blue */
.status-delivered {
  background: #9c27b0;
} /* Purple */
.status-confirmed {
  background: #4caf50;
} /* Green */
.status-cancelled {
  background: #f44336;
} /* Red */
```

### Escrow Status Display

```javascript
const escrowBadge = {
  HELD: "💰 Money held in escrow",
  RELEASED: "✅ Payment released to seller",
  REFUNDED: "🔄 Refunded to buyer",
};
```

### Buyer Dashboard Sections

1. **My Orders** - List all orders with status
2. **Wallet** - Balance, fund, withdraw, transaction history
3. **Browse** - Stores and products
4. **Order Details** - Track order progress

### Seller Dashboard Sections

1. **Pending Orders** - Orders awaiting acceptance
2. **Active Orders** - Accepted/Delivered orders
3. **Completed Orders** - Confirmed orders
4. **My Store** - Store info, products
5. **Earnings** - Wallet balance, withdrawal

---

## 🚀 Ready to Go!

1. ✅ Start server: `python manage.py runserver`
2. ✅ Open `api-tester.html` to test
3. ✅ Read `FRONTEND-API-GUIDE.md` for full docs
4. ✅ Connect your frontend app!

**Need help?** Check the API tester console for examples! 🎉
