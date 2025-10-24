# COVU Frontend API Integration Guide

> **Complete API documentation for connecting your frontend to the Order/Escrow backend**

## 📋 Table of Contents

- [Base URL & Authentication](#base-url--authentication)
- [Authentication APIs](#authentication-apis)
- [Wallet APIs](#wallet-apis)
- [Store APIs](#store-apis)
- [Product APIs](#product-apis)
- [Order & Escrow APIs](#order--escrow-apis)
- [Rating APIs](#rating-apis)
- [Common Response Formats](#common-response-formats)
- [Error Handling](#error-handling)

---

## Base URL & Authentication

### Base URL

```
http://localhost:8000/api
```

### Authentication

All authenticated endpoints require JWT token in header:

```
Authorization: Bearer <access_token>
```

### CORS Configuration

Your frontend URL must be added to `.env`:

```env
CORS_ALLOWED_ORIGINS=http://localhost:5500,http://localhost:3000
```

---

## Authentication APIs

### 1. Register User

```http
POST /api/auth/register/
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "password_confirm": "SecurePass123!",
  "full_name": "John Doe",
  "phone_number": "08012345678",
  "state": "lagos",
  "city": "Ikeja"
}
```

**Response (201 Created):**

```json
{
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "full_name": "John Doe",
    "phone_number": "08012345678",
    "state": "lagos",
    "city": "Ikeja",
    "is_seller": false
  },
  "tokens": {
    "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
  },
  "message": "Registration successful"
}
```

### 2. Login

```http
POST /api/auth/login/
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

**Response (200 OK):**

```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "full_name": "John Doe",
    "is_seller": false,
    "wallet_balance": "10000.00"
  }
}
```

### 3. Refresh Token

```http
POST /api/auth/token/refresh/
Content-Type: application/json

{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Response (200 OK):**

```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### 4. Get Current User Profile

```http
GET /api/auth/profile/
Authorization: Bearer <access_token>
```

**Response (200 OK):**

```json
{
  "id": "uuid",
  "email": "user@example.com",
  "full_name": "John Doe",
  "phone_number": "08012345678",
  "state": "lagos",
  "city": "Ikeja",
  "is_seller": false,
  "wallet_balance": "10000.00",
  "date_joined": "2025-10-21T10:30:00Z"
}
```

---

## Wallet APIs

### 1. Get Wallet Balance

```http
GET /api/wallet/balance/
Authorization: Bearer <access_token>
```

**Response (200 OK):**

```json
{
  "balance": "10000.00",
  "wallet_id": "uuid",
  "currency": "NGN"
}
```

### 2. Fund Wallet (Initialize Paystack Payment)

```http
POST /api/wallet/fund/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "amount": 5000
}
```

**Response (200 OK):**

```json
{
  "status": "success",
  "message": "Payment initialized",
  "authorization_url": "https://checkout.paystack.com/xxxxxx",
  "access_code": "xxxxx",
  "reference": "WALLET_FUND_1_ABC123"
}
```

**Frontend Flow:**

1. Call this endpoint to get `authorization_url`
2. Redirect user to Paystack checkout page
3. Paystack redirects back to your frontend callback URL
4. Backend webhook auto-credits wallet
5. Show success message to user

### 3. Get Transaction History

```http
GET /api/wallet/transactions/
Authorization: Bearer <access_token>
```

**Query Parameters:**

- `transaction_type` (optional): `CREDIT`, `DEBIT`, `REFUND`, `ESCROW_HOLD`
- `page` (optional): Page number (default: 1)
- `page_size` (optional): Items per page (default: 20)

**Response (200 OK):**

```json
{
  "count": 50,
  "next": "http://localhost:8000/api/wallet/transactions/?page=2",
  "previous": null,
  "results": [
    {
      "id": "uuid",
      "transaction_type": "CREDIT",
      "amount": "5000.00",
      "reference": "WALLET_FUND_1_ABC123",
      "description": "Wallet funding via Paystack",
      "balance_before": "5000.00",
      "balance_after": "10000.00",
      "created_at": "2025-10-21T10:30:00Z",
      "status": "completed"
    }
  ]
}
```

### 4. Add Bank Account

```http
POST /api/wallet/bank-accounts/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "account_number": "0123456789",
  "bank_code": "058"
}
```

**Response (201 Created):**

```json
{
  "id": "uuid",
  "account_number": "0123456789",
  "account_name": "John Doe",
  "bank_name": "GTBank",
  "bank_code": "058",
  "is_verified": true,
  "created_at": "2025-10-21T10:30:00Z"
}
```

### 5. List Bank Accounts

```http
GET /api/wallet/bank-accounts/
Authorization: Bearer <access_token>
```

**Response (200 OK):**

```json
[
  {
    "id": "uuid",
    "account_number": "0123456789",
    "account_name": "John Doe",
    "bank_name": "GTBank",
    "bank_code": "058",
    "is_verified": true,
    "created_at": "2025-10-21T10:30:00Z"
  }
]
```

### 6. Request Withdrawal

```http
POST /api/wallet/withdrawals/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "amount": 5000,
  "bank_account_id": "uuid"
}
```

**Response (201 Created):**

```json
{
  "id": "uuid",
  "amount": "5000.00",
  "fee": "100.00",
  "total_deducted": "5100.00",
  "bank_account": {
    "account_number": "0123456789",
    "account_name": "John Doe",
    "bank_name": "GTBank"
  },
  "status": "PENDING",
  "created_at": "2025-10-21T10:30:00Z",
  "message": "Withdrawal request submitted successfully"
}
```

**Withdrawal Fees (Tiered):**

- ₦2,000 - ₦9,999: ₦100
- ₦10,000 - ₦49,999: ₦150
- ₦50,000 - ₦99,999: ₦200
- ₦100,000 - ₦200,000: ₦250
- ₦200,000+: ₦300

---

## Store APIs

### 1. Create Store

```http
POST /api/stores/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "name": "Fashion Hub",
  "description": "Quality fashion items for everyone",
  "state": "lagos",
  "city": "Ikeja",
  "delivery_within_lga": 500,
  "delivery_outside_lga": 1500
}
```

**Response (201 Created):**

```json
{
  "id": "uuid",
  "name": "Fashion Hub",
  "description": "Quality fashion items for everyone",
  "seller": {
    "id": "uuid",
    "full_name": "John Doe",
    "email": "user@example.com"
  },
  "state": "lagos",
  "city": "Ikeja",
  "average_rating": "0.00",
  "product_count": 0,
  "delivery_within_lga": "500.00",
  "delivery_outside_lga": "1500.00",
  "is_active": true,
  "created_at": "2025-10-21T10:30:00Z"
}
```

### 2. List Stores (Location-based Algorithm)

```http
GET /api/stores/
```

**Query Parameters:**

- `state` (optional): Filter by state
- `city` (optional): Filter by city
- `search` (optional): Search store name/description
- `page` (optional): Page number

**Response (200 OK):**

```json
{
  "count": 50,
  "next": "http://localhost:8000/api/stores/?page=2",
  "previous": null,
  "results": [
    {
      "id": "uuid",
      "name": "Fashion Hub",
      "description": "Quality fashion items",
      "state": "lagos",
      "city": "Ikeja",
      "average_rating": "4.50",
      "product_count": 25,
      "delivery_within_lga": "500.00",
      "delivery_outside_lga": "1500.00",
      "created_at": "2025-10-21T10:30:00Z"
    }
  ]
}
```

### 3. Get Store Details

```http
GET /api/stores/{store_id}/
```

**Response (200 OK):**

```json
{
  "id": "uuid",
  "name": "Fashion Hub",
  "description": "Quality fashion items for everyone",
  "seller": {
    "id": "uuid",
    "full_name": "John Doe",
    "phone_number": "08012345678"
  },
  "state": "lagos",
  "city": "Ikeja",
  "average_rating": "4.50",
  "product_count": 25,
  "delivery_within_lga": "500.00",
  "delivery_outside_lga": "1500.00",
  "is_active": true,
  "created_at": "2025-10-21T10:30:00Z",
  "updated_at": "2025-10-22T15:45:00Z"
}
```

---

## Product APIs

### 1. Create Product

```http
POST /api/products/
Authorization: Bearer <access_token>
Content-Type: multipart/form-data

{
  "name": "Designer Dress",
  "description": "Beautiful red designer dress",
  "price": 15000,
  "category": "LADIES_CLOTHES",
  "images": <file>,
  "is_active": true
}
```

**Categories:**

- `MEN_CLOTHES`
- `LADIES_CLOTHES`
- `KIDS_CLOTHES`
- `BEAUTY`
- `ACCESSORIES`
- `BAGS`
- `WIGS`
- `SCENTS`
- `EXTRAS`

**Response (201 Created):**

```json
{
  "id": "uuid",
  "name": "Designer Dress",
  "description": "Beautiful red designer dress",
  "price": "15000.00",
  "category": "LADIES_CLOTHES",
  "images": "https://cloudinary.com/image.jpg",
  "store": {
    "id": "uuid",
    "name": "Fashion Hub"
  },
  "is_active": true,
  "created_at": "2025-10-21T10:30:00Z"
}
```

### 2. List Products

```http
GET /api/products/
```

**Query Parameters:**

- `store` (optional): Filter by store ID
- `category` (optional): Filter by category
- `min_price` (optional): Minimum price
- `max_price` (optional): Maximum price
- `search` (optional): Search product name/description
- `page` (optional): Page number

**Response (200 OK):**

```json
{
  "count": 100,
  "next": "http://localhost:8000/api/products/?page=2",
  "previous": null,
  "results": [
    {
      "id": "uuid",
      "name": "Designer Dress",
      "description": "Beautiful red designer dress",
      "price": "15000.00",
      "category": "LADIES_CLOTHES",
      "images": "https://cloudinary.com/image.jpg",
      "store": {
        "id": "uuid",
        "name": "Fashion Hub",
        "state": "lagos",
        "city": "Ikeja"
      },
      "is_active": true,
      "created_at": "2025-10-21T10:30:00Z"
    }
  ]
}
```

### 3. Get Product Details

```http
GET /api/products/{product_id}/
```

**Response (200 OK):**

```json
{
  "id": "uuid",
  "name": "Designer Dress",
  "description": "Beautiful red designer dress",
  "price": "15000.00",
  "category": "LADIES_CLOTHES",
  "images": "https://cloudinary.com/image.jpg",
  "store": {
    "id": "uuid",
    "name": "Fashion Hub",
    "seller": {
      "id": "uuid",
      "full_name": "John Doe"
    },
    "state": "lagos",
    "city": "Ikeja",
    "delivery_within_lga": "500.00",
    "delivery_outside_lga": "1500.00"
  },
  "is_active": true,
  "created_at": "2025-10-21T10:30:00Z",
  "updated_at": "2025-10-22T15:45:00Z"
}
```

---

## Order & Escrow APIs

### 1. Create Order (Buyer)

```http
POST /api/orders/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "product_id": "uuid",
  "delivery_address": "123 Main Street, Ikeja, Lagos"
}
```

**Response (201 Created):**

```json
{
  "id": "uuid",
  "order_number": "A1B2C3D4",
  "buyer": {
    "id": "uuid",
    "full_name": "Jane Buyer",
    "email": "buyer@example.com"
  },
  "seller": {
    "id": "uuid",
    "full_name": "John Seller",
    "email": "seller@example.com"
  },
  "product": {
    "id": "uuid",
    "name": "Designer Dress",
    "images": "https://cloudinary.com/image.jpg",
    "category": "LADIES_CLOTHES",
    "store_name": "Fashion Hub"
  },
  "quantity": 1,
  "product_price": "15000.00",
  "delivery_fee": "500.00",
  "total_amount": "15500.00",
  "status": "PENDING",
  "status_display": "Pending - Waiting Seller Acceptance",
  "delivery_address": "123 Main Street, Ikeja, Lagos",
  "escrow_status": "HELD",
  "escrow_amount": 15500.0,
  "created_at": "2025-10-21T10:30:00Z",
  "accepted_at": null,
  "delivered_at": null,
  "confirmed_at": null,
  "cancelled_at": null,
  "cancelled_by": null,
  "cancellation_reason": null
}
```

**What Happens:**

1. ✅ Buyer's wallet debited (₦15,500)
2. ✅ Money held in escrow (status: HELD)
3. ✅ Order created (status: PENDING)
4. ✅ Seller notified via email
5. ⏳ Waiting for seller to accept

### 2. List Orders (Buyer View)

```http
GET /api/orders/
Authorization: Bearer <access_token>
```

**Query Parameters:**

- `as_seller=true` - View orders as seller (default: buyer view)
- `status` - Filter by status: `PENDING`, `ACCEPTED`, `DELIVERED`, `CONFIRMED`, `CANCELLED`

**Response (200 OK):**

```json
{
  "count": 10,
  "view": "buyer",
  "results": [
    {
      "id": "uuid",
      "order_number": "A1B2C3D4",
      "buyer_name": "Jane Buyer",
      "seller_name": "John Seller",
      "product_name": "Designer Dress",
      "product_images": "https://cloudinary.com/image.jpg",
      "total_amount": "15500.00",
      "status": "PENDING",
      "status_display": "Pending - Waiting Seller Acceptance",
      "delivery_address": "123 Main Street, Ikeja, Lagos",
      "created_at": "2025-10-21T10:30:00Z"
    }
  ]
}
```

### 3. Get Order Details

```http
GET /api/orders/{order_id}/
Authorization: Bearer <access_token>
```

**Response (200 OK):**

```json
{
  "id": "uuid",
  "order_number": "A1B2C3D4",
  "buyer": {
    "id": "uuid",
    "full_name": "Jane Buyer",
    "email": "buyer@example.com",
    "phone_number": "08012345678"
  },
  "seller": {
    "id": "uuid",
    "full_name": "John Seller",
    "email": "seller@example.com",
    "phone_number": "08087654321"
  },
  "product": {
    "id": "uuid",
    "name": "Designer Dress",
    "images": "https://cloudinary.com/image.jpg",
    "category": "LADIES_CLOTHES",
    "store_name": "Fashion Hub"
  },
  "quantity": 1,
  "product_price": "15000.00",
  "delivery_fee": "500.00",
  "total_amount": "15500.00",
  "status": "PENDING",
  "status_display": "Pending - Waiting Seller Acceptance",
  "delivery_address": "123 Main Street, Ikeja, Lagos",
  "escrow_status": "HELD",
  "escrow_amount": 15500.0,
  "created_at": "2025-10-21T10:30:00Z",
  "accepted_at": null,
  "delivered_at": null,
  "confirmed_at": null,
  "cancelled_at": null,
  "cancelled_by": null,
  "cancellation_reason": null
}
```

### 4. Accept Order (Seller)

```http
POST /api/orders/{order_id}/accept/
Authorization: Bearer <access_token>
```

**Response (200 OK):**

```json
{
  "status": "success",
  "message": "Order accepted successfully",
  "order": {
    "id": "uuid",
    "order_number": "A1B2C3D4",
    "status": "ACCEPTED",
    "status_display": "Accepted - Seller Preparing Order",
    "accepted_at": "2025-10-21T11:00:00Z",
    "escrow_status": "HELD"
  }
}
```

**What Happens:**

1. ✅ Order status: PENDING → ACCEPTED
2. ✅ Buyer notified via email
3. ⏳ Money still held in escrow

### 5. Mark as Delivered (Seller)

```http
POST /api/orders/{order_id}/deliver/
Authorization: Bearer <access_token>
```

**Response (200 OK):**

```json
{
  "status": "success",
  "message": "Order marked as delivered",
  "order": {
    "id": "uuid",
    "order_number": "A1B2C3D4",
    "status": "DELIVERED",
    "status_display": "Delivered - Waiting Buyer Confirmation",
    "delivered_at": "2025-10-21T14:00:00Z",
    "escrow_status": "HELD"
  }
}
```

**What Happens:**

1. ✅ Order status: ACCEPTED → DELIVERED
2. ✅ Buyer notified via email
3. ⏳ Money still held in escrow (waiting buyer confirmation)

### 6. Confirm Delivery (Buyer)

```http
POST /api/orders/{order_id}/confirm/
Authorization: Bearer <access_token>
```

**Response (200 OK):**

```json
{
  "status": "success",
  "message": "Order confirmed, payment released to seller",
  "order": {
    "id": "uuid",
    "order_number": "A1B2C3D4",
    "status": "CONFIRMED",
    "status_display": "Confirmed - Transaction Complete",
    "confirmed_at": "2025-10-21T15:00:00Z",
    "escrow_status": "RELEASED"
  }
}
```

**What Happens:**

1. ✅ Order status: DELIVERED → CONFIRMED
2. ✅ Escrow released (HELD → RELEASED)
3. ✅ Seller's wallet credited (₦15,500)
4. ✅ Seller notified via email
5. 🎉 Transaction complete!

### 7. Cancel Order

```http
POST /api/orders/{order_id}/cancel/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "reason": "Changed my mind"
}
```

**Response (200 OK):**

```json
{
  "status": "success",
  "message": "Order cancelled, refund processed",
  "order": {
    "id": "uuid",
    "order_number": "A1B2C3D4",
    "status": "CANCELLED",
    "cancelled_at": "2025-10-21T12:00:00Z",
    "cancelled_by": "BUYER",
    "cancellation_reason": "Changed my mind",
    "escrow_status": "REFUNDED"
  }
}
```

**Cancellation Rules:**

- **Buyer**: Can cancel only while status is `PENDING`
- **Seller**: Can cancel anytime before `CONFIRMED`

**What Happens:**

1. ✅ Order status → CANCELLED
2. ✅ Escrow refunded (HELD → REFUNDED)
3. ✅ Buyer's wallet refunded (₦15,500)
4. ✅ Both parties notified via email

### 8. Get Order Statistics

```http
GET /api/orders/stats/
Authorization: Bearer <access_token>
```

**Response (200 OK):**

```json
{
  "buyer": {
    "total": 25,
    "pending": 3,
    "accepted": 5,
    "delivered": 2,
    "confirmed": 12,
    "cancelled": 3
  },
  "seller": {
    "total": 50,
    "pending": 10,
    "accepted": 15,
    "delivered": 8,
    "confirmed": 12,
    "cancelled": 5
  }
}
```

---

## Rating APIs

### 1. Create Rating (After Order Confirmed)

```http
POST /api/ratings/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "order_id": "uuid",
  "rating": 5,
  "comment": "Excellent service! Fast delivery"
}
```

**Response (201 Created):**

```json
{
  "id": "uuid",
  "order": "uuid",
  "store": {
    "id": "uuid",
    "name": "Fashion Hub"
  },
  "buyer": {
    "id": "uuid",
    "full_name": "Jane Buyer"
  },
  "rating": 5,
  "comment": "Excellent service! Fast delivery",
  "created_at": "2025-10-21T16:00:00Z"
}
```

### 2. List Store Ratings

```http
GET /api/ratings/?store={store_id}
```

**Response (200 OK):**

```json
{
  "count": 50,
  "results": [
    {
      "id": "uuid",
      "buyer": {
        "full_name": "Jane Buyer"
      },
      "rating": 5,
      "comment": "Excellent service! Fast delivery",
      "created_at": "2025-10-21T16:00:00Z"
    }
  ]
}
```

---

## Common Response Formats

### Success Response

```json
{
  "status": "success",
  "message": "Operation completed successfully",
  "data": {}
}
```

### Error Response

```json
{
  "error": "Error message here",
  "details": {
    "field_name": ["Error details"]
  }
}
```

---

## Error Handling

### HTTP Status Codes

- `200 OK` - Success
- `201 Created` - Resource created
- `400 Bad Request` - Validation error
- `401 Unauthorized` - Not authenticated
- `403 Forbidden` - Not authorized
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error

### Common Errors

#### Insufficient Funds

```json
{
  "error": "Insufficient funds. Need ₦15500.00, have ₦10000.00"
}
```

#### Invalid Order Status

```json
{
  "error": "Cannot accept order. Current status: ACCEPTED, expected: PENDING"
}
```

#### Permission Denied

```json
{
  "error": "You can only confirm your own orders"
}
```

#### Buyer Buying from Own Store

```json
{
  "error": "You cannot buy from your own store"
}
```

---

## Complete Order Flow Example

### Frontend Implementation Steps

**1. Buyer Places Order**

```javascript
// Step 1: Get product details
const product = await fetch(`/api/products/${productId}/`);

// Step 2: Check buyer's wallet balance
const wallet = await fetch("/api/wallet/balance/", {
  headers: { Authorization: `Bearer ${token}` },
});

// Step 3: Create order
const order = await fetch("/api/orders/", {
  method: "POST",
  headers: {
    Authorization: `Bearer ${token}`,
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    product_id: productId,
    delivery_address: "123 Main Street, Lagos",
  }),
});

// Success! Money deducted, held in escrow
// Show: "Order placed successfully! Waiting for seller to accept"
```

**2. Seller Accepts Order**

```javascript
// Seller sees notification
const orders = await fetch("/api/orders/?as_seller=true", {
  headers: { Authorization: `Bearer ${sellerToken}` },
});

// Seller accepts
const result = await fetch(`/api/orders/${orderId}/accept/`, {
  method: "POST",
  headers: { Authorization: `Bearer ${sellerToken}` },
});

// Show: "Order accepted! Start preparing"
```

**3. Seller Marks as Delivered**

```javascript
const result = await fetch(`/api/orders/${orderId}/deliver/`, {
  method: "POST",
  headers: { Authorization: `Bearer ${sellerToken}` },
});

// Show: "Marked as delivered! Buyer will confirm"
```

**4. Buyer Confirms Delivery**

```javascript
const result = await fetch(`/api/orders/${orderId}/confirm/`, {
  method: "POST",
  headers: { Authorization: `Bearer ${buyerToken}` },
});

// Success! Escrow released to seller
// Show: "Thank you! Payment released to seller"
```

---

## Environment Setup

### 1. Update CORS in `.env`

```env
# Add your frontend URL
CORS_ALLOWED_ORIGINS=http://localhost:5500,http://localhost:3000,https://yourdomain.com
```

### 2. Start Backend Server

```bash
python manage.py runserver
```

### 3. Test Connection

```javascript
// Test if backend is accessible
fetch("http://localhost:8000/api/stores/")
  .then((res) => res.json())
  .then((data) => console.log("Backend connected!", data))
  .catch((err) => console.error("Connection failed:", err));
```

---

## Testing Credentials

**Buyer Account:**

- Email: `buyer@test.com`
- Password: `testpass123`
- Wallet Balance: ₦10,000

**Seller Account:**

- Email: `seller@test.com`
- Password: `testpass123`
- Has store with 3 products

---

## Need Help?

- Check `README.md` for project overview
- Check `DEVELOPMENT-GUIDE.md` for implementation details
- Check `TESTING-RESULTS.md` for test scenarios

**Backend is ready for frontend integration!** 🚀
