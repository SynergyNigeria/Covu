# URGENT FIX: Wallet Top-Up Issues

## Problems Identified

### Issue 1: Still Getting 401 Unauthorized ❌

**Root Cause**: Django server not reloaded after code changes
**Solution**: Restart Django server

### Issue 2: Balance Not Updated After Payment ❌

**Root Cause**: Paystack webhooks don't work on localhost (127.0.0.1)
**Solution**: Use manual verification endpoint as primary method

---

## IMMEDIATE FIXES

### Fix 1: Restart Django Server

**Stop Django** (Ctrl+C in terminal) then restart:

```bash
cd C:\Users\DELL\Desktop\Backend
.\venv\Scripts\activate
python manage.py runserver
```

This will load the updated `permission_classes = []` fix.

### Fix 2: Update Frontend to Use Verification Endpoint

Since webhooks don't work on localhost, we need to rely on the verification endpoint to credit the wallet.

**File**: `frontend/assets/js/purchase.js`

Change the flow to:

1. Wait 2 seconds for webhook attempt
2. **Always call verification endpoint** (don't wait for webhook)
3. Verification will credit wallet if not already done

---

## Why Webhooks Don't Work on Localhost

```
Paystack Server (Cloud)
        ↓
        ↓ Tries to send webhook to:
        ↓ http://127.0.0.1:8000/api/wallet/webhook/
        ↓
        ❌ FAILS: 127.0.0.1 is YOUR computer, not accessible from internet
```

**Solutions**:

1. **Development**: Use verification endpoint (manual trigger)
2. **Production**: Deploy to public URL, webhooks will work

---

## Updated Frontend Code

**File**: `frontend/assets/js/purchase.js`

```javascript
// Check if returning from Paystack payment
const urlParams = new URLSearchParams(window.location.search);
const paymentStatus = urlParams.get("payment");
const reference = urlParams.get("ref");

if (paymentStatus === "success" && reference) {
  showToast("Payment successful! Updating wallet...", "success");

  // Clean URL immediately
  window.history.replaceState({}, document.title, window.location.pathname);

  // Wait briefly (webhook won't work on localhost anyway)
  await new Promise((resolve) => setTimeout(resolve, 1000));

  // PRIMARY: Call verification endpoint to credit wallet
  try {
    const verifyResponse = await api.get(`/wallet/verify/${reference}/`);
    console.log("✅ Payment verified:", verifyResponse);

    if (verifyResponse.status === "success") {
      // Verification credited wallet or confirmed already credited
      showToast(
        `Wallet credited: ${formatCurrency(verifyResponse.amount)}`,
        "success"
      );

      // Refresh balance
      try {
        const updatedUser = await api.get(API_CONFIG.ENDPOINTS.PROFILE);
        localStorage.setItem(
          API_CONFIG.TOKEN_KEYS.USER,
          JSON.stringify(updatedUser)
        );

        const walletElement = document.getElementById("walletBalance");
        if (walletElement) {
          walletElement.textContent = formatCurrency(
            updatedUser.wallet_balance
          );
        }

        showToast("Balance updated!", "success");
      } catch (e) {
        console.error("Error refreshing balance:", e);
        showToast("Please refresh page to see updated balance", "info");
      }
    }
  } catch (error) {
    console.error("❌ Verification error:", error);
    showToast("Payment processed! Please refresh page to see balance.", "info");
  }
}
```

---

## Testing After Fixes

### Test 1: Restart Server

```bash
# In Backend terminal
# Press Ctrl+C to stop Django
# Then run:
python manage.py runserver
```

### Test 2: Try Payment Again

1. Go to purchase page
2. Click "Top Up" → ₦1000
3. Complete payment on Paystack
4. You'll be redirected back
5. **Expected**:
   - ✅ No logout
   - ✅ Verification endpoint called
   - ✅ Wallet credited
   - ✅ Balance updated

### Test 3: Verify No Double Credit

1. After successful payment, copy reference from console log
2. Call: `GET /api/wallet/verify/<reference>/` again
3. **Expected**: Returns "Payment already processed", no double credit

---

## Production Deployment Notes

When you deploy to production (e.g., Heroku, DigitalOcean, etc.):

1. **Webhooks WILL work** (because public URL)
2. **Keep verification as fallback** (in case webhook fails)
3. **Update Paystack callback URL** to production URL
4. **Configure Paystack webhook URL** in Paystack dashboard

Example production flow:

```
User pays → Paystack webhook credits wallet (fast) ✅
         → User returns → Verification checks if already credited ✅
         → Balance updated ✅
```

---

## Monitoring

After restart, check logs for:

```bash
# Should see this when verification is called:
✅ Wallet credited (manual): admin@gmail.com - ₦3000.00 - Ref: WALLET_FUND_xxx

# Should NOT see:
❌ WARNING 2025-11-06 05:41:09,555 Unauthorized: /api/wallet/verify/
```

---

## Summary

**Right Now (Localhost)**:

- Webhooks: ❌ Won't work (can't reach 127.0.0.1)
- Verification: ✅ Works (called by frontend)
- Balance Update: ✅ Manual verification credits wallet

**Production**:

- Webhooks: ✅ Will work (public URL)
- Verification: ✅ Fallback if webhook fails
- Balance Update: ✅ Automatic

**Next Steps**:

1. Restart Django server ✅
2. Update frontend to prioritize verification ✅
3. Test payment flow ✅
4. Deploy to production for webhook support ✅
