# Paystack Webhook - Localhost Limitation 🔧

**Date:** October 23, 2025  
**Issue:** Webhook not crediting wallet on localhost

---

## The Problem

### ❌ **Paystack Webhooks Don't Work on Localhost**

**Why?**

- Webhooks require a **public URL** that Paystack servers can reach
- `http://localhost:8000` is only accessible on your computer
- Paystack servers can't call your webhook at `http://localhost:8000/api/wallet/webhook/`

**What This Means:**

- ✅ Payment initialization works (frontend → backend → Paystack)
- ✅ User completes payment on Paystack
- ❌ Webhook doesn't get called (Paystack can't reach localhost)
- ❌ Wallet doesn't get credited automatically

---

## Solutions

### Solution 1: Manual Verification Endpoint ✅ (Current)

**How It Works:**

1. User completes payment on Paystack
2. Paystack redirects back to your site with reference
3. Frontend calls `/api/wallet/verify/{reference}/`
4. Backend calls Paystack API to verify payment
5. Backend credits wallet manually

**Implementation:**

```javascript
// Frontend: purchase.js
const verifyResponse = await api.get(`/wallet/verify/${reference}/`);
```

```python
# Backend: wallets/views.py - VerifyPaymentView
def get(self, request, reference):
    # Call Paystack verification API
    response = requests.get(
        f'https://api.paystack.co/transaction/verify/{reference}',
        headers={'Authorization': f'Bearer {PAYSTACK_SECRET_KEY}'}
    )

    # If successful, credit wallet
    if response.data['status'] == 'success':
        # Create CREDIT transaction
        WalletTransaction.objects.create(...)
```

---

### Solution 2: Use Ngrok for Local Development 🌐

**Ngrok** creates a public URL that forwards to your localhost.

**Steps:**

1. **Install Ngrok:**

   ```bash
   # Download from https://ngrok.com/download
   # Or install via scoop:
   scoop install ngrok
   ```

2. **Run Ngrok:**

   ```bash
   ngrok http 8000
   ```

   Output:

   ```
   Forwarding: https://abc123.ngrok.io -> http://localhost:8000
   ```

3. **Update .env:**

   ```bash
   # Use the ngrok URL
   FRONTEND_URL=https://abc123.ngrok.io
   ```

4. **Configure Paystack Webhook:**

   - Go to Paystack Dashboard → Settings → Webhooks
   - Set webhook URL: `https://abc123.ngrok.io/api/wallet/webhook/`
   - Save

5. **Restart Backend:**
   ```bash
   python manage.py runserver
   ```

**Now webhooks will work!** 🎉

---

### Solution 3: Deploy to Production 🚀

For production, you'll have a real domain (e.g., `https://yourapp.com`).

**Steps:**

1. **Deploy Backend:**

   - Use Heroku, Railway, DigitalOcean, etc.
   - Get public URL: `https://api.yourapp.com`

2. **Update .env:**

   ```bash
   FRONTEND_URL=https://yourapp.com
   ```

3. **Configure Paystack Webhook:**

   - Paystack Dashboard → Settings → Webhooks
   - Set: `https://api.yourapp.com/api/wallet/webhook/`

4. **Test:**
   - Payment → Webhook automatically credits wallet ✅

---

## Current Flow (Manual Verification)

```
┌─────────────┐
│   User      │
│  Pays ₦50K  │
└──────┬──────┘
       │
       │ 1. Payment successful on Paystack
       ▼
┌──────────────────────┐
│  Paystack redirects  │
│  to purchase.html    │
│  ?payment=success    │
│  &ref=WALLET_FUND... │
└──────┬───────────────┘
       │
       │ 2. Frontend detects success
       ▼
┌──────────────────────────┐
│  Frontend calls:         │
│  GET /api/wallet/verify/ │
│      {reference}/        │
└──────┬───────────────────┘
       │
       │ 3. Backend verifies with Paystack API
       ▼
┌──────────────────────────┐
│  Backend:                │
│  - Calls Paystack API    │
│  - Confirms payment      │
│  - Credits wallet        │
│  - Creates transaction   │
└──────┬───────────────────┘
       │
       │ 4. Returns success
       ▼
┌──────────────────────┐
│  Frontend:           │
│  - Refreshes balance │
│  - Shows toast       │
└──────────────────────┘
```

---

## Troubleshooting

### Issue: 500 Error on `/wallet/verify/{reference}/`

**Possible Causes:**

1. **Paystack API timeout**

   - Solution: Check internet connection
   - Solution: Try again

2. **Invalid reference**

   - Check reference format: `WALLET_FUND_{user_id}_{random}`
   - Verify it matches what Paystack returned

3. **Paystack API error**
   - Check Paystack status: https://status.paystack.com/
   - Check Paystack secret key in .env

**Debug Steps:**

1. **Check Backend Logs:**

   ```bash
   # In terminal where backend is running
   # Look for ERROR messages
   ```

2. **Test Verification Manually:**

   ```bash
   # Replace {reference} with actual reference
   curl -H "Authorization: Bearer {your_jwt_token}" \
        http://localhost:8000/api/wallet/verify/WALLET_FUND_11_32EA70E6D083/
   ```

3. **Check Paystack Dashboard:**
   - Go to Paystack Dashboard → Transactions
   - Find your payment
   - Verify status is "success"

---

### Issue: Wallet Balance Not Updating

**Possible Causes:**

1. **Verification failed (500 error)**

   - Check backend logs for error details
   - Try manual verification again

2. **Profile data not refreshing**

   - Check `GET /api/auth/profile/` response
   - Verify `wallet_balance` field is included

3. **Display not updating**
   - Check `document.getElementById('walletBalance')`
   - Verify element exists on page

**Solutions:**

1. **Manual Refresh:**

   ```
   Press F5 to reload page
   Wallet balance should update
   ```

2. **Check Balance via API:**

   ```bash
   curl -H "Authorization: Bearer {your_jwt_token}" \
        http://localhost:8000/api/wallet/
   ```

3. **Check Transactions:**
   ```bash
   curl -H "Authorization: Bearer {your_jwt_token}" \
        http://localhost:8000/api/wallet/transactions/
   ```

---

## Testing Checklist

### ✅ Payment Initialization

- [ ] Click "Top Up" button
- [ ] Enter amount (e.g., 50000)
- [ ] Redirects to Paystack payment page

### ✅ Payment Completion

- [ ] Enter test card details
- [ ] Payment successful on Paystack
- [ ] Email received from Paystack

### ✅ Redirect Back

- [ ] Automatically redirected to purchase.html
- [ ] URL includes `?payment=success&ref=...`

### ✅ Verification & Credit

- [ ] Green success toast appears
- [ ] Backend logs: "Wallet credited (manual)..."
- [ ] Wallet balance updates on page

### ✅ Database Check

- [ ] Check `wallets_wallettransaction` table
- [ ] Verify CREDIT transaction exists
- [ ] Check `balance_after` field

---

## Backend Logs to Watch For

### Success:

```
INFO Paystack payment initialized: papa@gmail.com - ₦50000.00 - Ref: WALLET_FUND_11_...
INFO Wallet credited (manual): papa@gmail.com - ₦50,000.00 - Ref: WALLET_FUND_11_...
```

### Webhook (Won't work on localhost):

```
WARNING Paystack webhook received without signature
# or
INFO Paystack webhook received: charge.success
INFO Wallet credited: papa@gmail.com - ₦50,000.00 - Ref: WALLET_FUND_11_...
```

### Errors:

```
ERROR Paystack verification error: Connection timeout
ERROR Failed to send email notification: ...
```

---

## Quick Fix If Balance Not Showing

**Option 1: Refresh Page**

```
Press F5
```

**Option 2: Logout and Login**

```
1. Logout
2. Login again
3. Check wallet balance
```

**Option 3: Direct API Call**

```bash
# Check wallet directly
curl -H "Authorization: Bearer YOUR_TOKEN" \
     http://localhost:8000/api/wallet/

# Response should show updated balance
{
  "balance": "50000.00"
}
```

---

## Recommended Solution for Development

**Use Ngrok** (Solution 2) - This makes webhooks work on localhost!

```bash
# 1. Install Ngrok
scoop install ngrok

# 2. Run Ngrok
ngrok http 8000

# 3. Update .env with ngrok URL
FRONTEND_URL=https://abc123.ngrok.io

# 4. Configure Paystack webhook
# Paystack Dashboard → Webhooks
# URL: https://abc123.ngrok.io/api/wallet/webhook/

# 5. Restart backend
python manage.py runserver

# 6. Test payment - webhook will work! ✅
```

---

## For Production

1. ✅ Deploy backend to public server
2. ✅ Get real domain (e.g., api.yourapp.com)
3. ✅ Configure Paystack webhook with real URL
4. ✅ Webhooks work automatically
5. ✅ No manual verification needed

---

**Current Status:**

- ✅ Payment initialization working
- ✅ Paystack payment working
- ✅ Redirect back working
- ❌ Webhook not working (localhost limitation)
- ✅ Manual verification working (fallback)

**Recommendation:** Use Ngrok for local development to test webhooks properly!
