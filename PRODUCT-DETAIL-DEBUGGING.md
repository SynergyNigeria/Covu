# Product Detail Page - Debugging Guide

## Current Status

The product detail page is showing "Failed to load product detail" error. Let's debug step by step.

## Debugging Steps

### Step 1: Open Browser Console

1. Open the products page: `http://127.0.0.1:5500/frontend/templates/products.html`
2. Press `F12` to open Developer Tools
3. Go to the **Console** tab

### Step 2: Click on a Product

1. Click on any product card
2. You should be redirected to: `product-detail.html?id=SOME-UUID`
3. Check the console for these messages:

**Expected Console Output:**

```
Product ID from URL: abc123-def456-ghi789
Fetching from endpoint: /products/abc123-def456-ghi789/
Full URL: http://localhost:8000/api/products/abc123-def456-ghi789/
API Response: {...}
```

### Step 3: Check What's in the Console

#### Case A: "Product ID from URL: null"

**Problem:** Product ID is not in the URL
**Solution:** Check that products.js is passing the ID correctly
**Action:** Look at the URL bar - does it have `?id=something`?

#### Case B: "API Response: { success: false, message: '...' }"

**Problem:** Backend returned an error
**Possible Causes:**

1. Backend server not running
2. Product doesn't exist
3. Authentication issue
4. Wrong endpoint

#### Case C: Network Error or 404

**Problem:** Can't reach the backend
**Check:**

1. Is Django server running on `http://localhost:8000`?
2. Run: `python manage.py runserver`

#### Case D: 401 Unauthorized

**Problem:** Not logged in or token expired
**Solution:** Log out and log back in

---

## Quick Fixes

### Fix 1: Make Sure Backend is Running

```powershell
cd C:\Users\DELL\Desktop\Backend
python manage.py runserver
```

You should see:

```
Starting development server at http://127.0.0.1:8000/
```

### Fix 2: Test the Endpoint Directly

Open a new browser tab and go to:

```
http://localhost:8000/api/products/
```

You should see a list of products. Each product has an `id` field.

Copy one of the IDs and test the detail endpoint:

```
http://localhost:8000/api/products/THE-PRODUCT-ID/
```

You should see that product's full details.

### Fix 3: Check Authentication

The console logs will show if authentication is working. Look for:

- "Authorization: Bearer ..." in the Network tab
- Any 401 errors

### Fix 4: Verify Product IDs Exist

In the products list API response, check that products have valid UUIDs:

```json
{
    "results": [
        {
            "id": "123e4567-e89b-12d3-a456-426614174000",  // <-- This should be a valid UUID
            "name": "Product Name",
            ...
        }
    ]
}
```

---

## What to Check in Console

### 1. Product ID from URL

```javascript
Product ID from URL: 123e4567-e89b-12d3-a456-426614174000
```

✅ **Good:** ID is present and looks like a UUID  
❌ **Bad:** ID is null, undefined, or not a UUID

### 2. Endpoint URL

```javascript
Full URL: http://localhost:8000/api/products/123e4567-e89b-12d3-a456-426614174000/
```

✅ **Good:** URL is correctly formed  
❌ **Bad:** URL is missing parts or has double slashes

### 3. API Response

```javascript
API Response: { success: true, data: {...} }
```

✅ **Good:** Success is true, data contains product info  
❌ **Bad:** Success is false or data is missing

---

## Network Tab Inspection

### Step 1: Open Network Tab

1. Press F12
2. Click "Network" tab
3. Refresh the product detail page
4. Look for the request to `/api/products/SOME-ID/`

### Step 2: Check Request Details

Click on the request and check:

**Request URL:** Should be `http://localhost:8000/api/products/UUID/`

**Request Headers:** Should include:

```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

**Status Code:**

- `200 OK` ✅ - Working!
- `404 Not Found` ❌ - Product doesn't exist
- `401 Unauthorized` ❌ - Not logged in
- `500 Server Error` ❌ - Backend error

**Response:**
Should be JSON with product details:

```json
{
    "id": "uuid",
    "name": "Product Name",
    "description": "...",
    "price": "5000.00",
    "store_info": {...}
}
```

---

## Common Issues & Solutions

### Issue 1: "Failed to load product detail"

**Check:** Console for specific error
**Fix:** See which case above matches your console output

### Issue 2: Network tab shows 404

**Problem:** Product doesn't exist or wrong URL
**Fix:**

1. Check that the product ID in URL is valid
2. Verify product exists: `http://localhost:8000/api/products/`
3. Make sure backend URL is correct in config.js

### Issue 3: Network tab shows 401

**Problem:** Not authenticated
**Fix:**

1. Log out
2. Log back in
3. Try again

### Issue 4: Network tab shows 500

**Problem:** Backend error
**Fix:**

1. Check Django console for error traceback
2. Look for Python errors
3. Check that ProductDetailSerializer is working

### Issue 5: "Product ID from URL: null"

**Problem:** URL doesn't have ?id= parameter
**Fix:**

1. Check products.js line 310
2. Verify it's: `product-detail.html?id=${product.id}`
3. Check that product.id exists in the data

### Issue 6: Page loads but shows "Loading..."

**Problem:** populateProductDetails() not called
**Fix:**

1. Check console for errors
2. Verify response.success is true
3. Check that response.data exists

---

## Testing Checklist

Run through these tests:

### ✅ Backend Tests

- [ ] Django server is running on port 8000
- [ ] Can access: `http://localhost:8000/api/products/`
- [ ] Products list shows products with valid UUIDs
- [ ] Can access product detail by ID
- [ ] Response includes store_info

### ✅ Frontend Tests

- [ ] Live Server is running on port 5500
- [ ] Products page loads and shows products
- [ ] Clicking a product shows URL with ?id=UUID
- [ ] Console shows "Product ID from URL: UUID"
- [ ] Console shows "Fetching from endpoint"
- [ ] Console shows "API Response"

### ✅ Authentication Tests

- [ ] User is logged in
- [ ] Access token exists in localStorage
- [ ] Network request includes Authorization header
- [ ] No 401 errors

---

## Manual Test

### Test 1: Direct API Call

Open browser console on products page and run:

```javascript
// Get a product ID from the list
const productId = allProducts[0].id;
console.log("Testing with ID:", productId);

// Test the API call
const endpoint = API_CONFIG.ENDPOINTS.PRODUCT_DETAIL(productId);
console.log("Endpoint:", endpoint);

api.get(endpoint).then((response) => {
  console.log("Test result:", response);
});
```

This will show you if the API call works.

### Test 2: Check Product Data

On the products page console:

```javascript
// Check if products have IDs
console.log("First product:", allProducts[0]);
console.log("Product ID:", allProducts[0].id);
console.log("ID type:", typeof allProducts[0].id);
```

Should show:

```
First product: {id: "123e...", name: "...", ...}
Product ID: 123e4567-e89b-12d3-a456-426614174000
ID type: string
```

---

## What to Report

If you're still having issues, share:

1. **Console Output:** Copy all console.log messages
2. **Network Request:** Status code and response
3. **URL in Browser:** The full URL showing
4. **Backend Console:** Any Django errors

With these details, we can pinpoint the exact issue!

---

## Expected Working Flow

1. ✅ Products page loads
2. ✅ Click product → Navigate to `product-detail.html?id=UUID`
3. ✅ Console: "Product ID from URL: UUID"
4. ✅ Console: "Fetching from endpoint: /products/UUID/"
5. ✅ Network: GET request to backend
6. ✅ Backend: Returns 200 OK with product data
7. ✅ Console: "API Response: { success: true, data: {...} }"
8. ✅ Console: "Current product: {...}"
9. ✅ Page: Shows product details

If ANY step fails, check that specific step in the debugging guide above!
