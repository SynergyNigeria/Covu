# 🚀 COVU Production Deployment Checklist

## ✅ Current Status

### Already Configured (LIVE):

- ✅ **Paystack Live Keys** - sk*live*... and pk*live*...
- ✅ **Wallet Deposits** - Users can fund wallet via Paystack
- ✅ **Wallet Withdrawals** - Users can withdraw to bank accounts
- ✅ **Email Notifications** - Zoho SMTP configured
- ✅ **Async Email** - Celery + Redis for background processing
- ✅ **Order System** - Complete order flow with emails

---

## 🔧 Production Settings To Update

### 1. **Set DEBUG to False**

In `.env` file:

```env
DEBUG=False
```

⚠️ **IMPORTANT**: Only set this when deploying to production server!

### 2. **Configure Allowed Hosts**

In `.env` add:

```env
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com,api.yourdomain.com
```

### 3. **Set Secret Key** (if not already done)

Generate a new secret key for production:

```python
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Add to `.env`:

```env
SECRET_KEY=your-generated-secret-key-here
```

### 4. **Configure Paystack Webhook**

In Paystack Dashboard:

1. Go to **Settings → Webhooks**
2. Add webhook URL: `https://yourdomain.com/api/wallet/webhook/`
3. Add transfer webhook URL: `https://yourdomain.com/api/wallet/transfer-webhook/`
4. Events to listen for:
   - `charge.success` (for deposits)
   - `transfer.success` (for withdrawals)
   - `transfer.failed` (for withdrawal failures)

### 5. **Update Frontend URL**

In `.env`:

```env
FRONTEND_URL=https://yourdomain.com
```

This is used for Paystack callback redirects.

---

## 💰 How Deposits Work (Already Implemented)

### User Flow:

1. User clicks "Fund Wallet"
2. Enters amount (e.g., ₦5,000)
3. **Frontend** calls: `POST /api/wallet/fund/`
4. **Backend** returns Paystack payment URL
5. User redirects to Paystack, pays
6. Paystack sends webhook to: `/api/wallet/webhook/`
7. **Backend** automatically credits wallet
8. User receives email confirmation

### Test it:

```bash
# From frontend or Postman
POST http://localhost:8000/api/wallet/fund/
Authorization: Bearer <user-token>
Content-Type: application/json

{
  "amount": 5000.00
}

# Response:
{
  "status": "success",
  "message": "Payment initialized...",
  "data": {
    "authorization_url": "https://checkout.paystack.com/...",
    "reference": "WALLET_FUND_...",
    "amount": 5000.00
  }
}
```

---

## 💸 How Withdrawals Work (Already Implemented)

### Prerequisites:

1. User must add bank account first

### Add Bank Account:

```bash
POST http://localhost:8000/api/wallet/bank-accounts/
Authorization: Bearer <user-token>

{
  "bank_name": "GTBank",
  "bank_code": "058",
  "account_number": "0123456789",
  "is_default": true
}

# Backend verifies with Paystack and creates transfer recipient
```

### Request Withdrawal:

```bash
POST http://localhost:8000/api/wallet/withdraw/
Authorization: Bearer <user-token>

{
  "amount": 10000.00,
  "bank_account_id": "uuid-of-bank-account"
}

# Backend:
# 1. Validates balance (amount + fee)
# 2. Initiates Paystack transfer
# 3. Debits wallet immediately
# 4. Sends email notification
# 5. Waits for webhook confirmation
```

### Withdrawal Fees (Tiered):

- **₦2K - ₦9,999**: ₦100 fee (₦50 Paystack + ₦50 Platform)
- **₦10K - ₦49,999**: ₦150 fee (₦50 Paystack + ₦100 Platform)
- **₦50K - ₦99,999**: ₦200 fee (₦50 Paystack + ₦150 Platform)
- **₦100K - ₦200K**: ₦250 fee (₦50 Paystack + ₦200 Platform)
- **₦200K+**: ₦300 fee (₦50 Paystack + ₦250 Platform)

---

## 🧪 Testing in Production

### Test Deposits:

1. Create a test user account
2. Fund wallet with small amount (₦100)
3. Check:
   - Paystack payment successful
   - Wallet credited automatically
   - Email received
   - Transaction history updated

### Test Withdrawals:

1. Add bank account
2. Verify account name appears correctly
3. Request withdrawal (₦200 minimum)
4. Check:
   - Wallet debited immediately
   - Email received (initiated)
   - Money arrives in bank (within 24hrs)
   - Email received (completed)
   - Transaction history updated

---

## 📧 Email Notifications (Already Working)

### Wallet Emails:

- ✅ **Wallet Funded** - When deposit successful
- ✅ **Withdrawal Initiated** - When withdrawal requested
- ✅ **Withdrawal Completed** - When money arrives
- ✅ **Withdrawal Failed** - If transfer fails (auto-refund)

### Order Emails:

- ✅ **Order Created** - Seller notified
- ✅ **Order Accepted** - Buyer notified
- ✅ **Order Delivered** - Buyer notified
- ✅ **Order Confirmed** - Seller notified (payment released)
- ✅ **Order Cancelled** - Both parties notified

---

## 🔒 Security Features

### Already Implemented:

- ✅ **Webhook Signature Verification** - Prevents fake webhooks
- ✅ **Idempotency** - Prevents duplicate transactions
- ✅ **Atomic Transactions** - Database consistency
- ✅ **Authentication Required** - All endpoints protected
- ✅ **Balance Validation** - Can't withdraw more than balance
- ✅ **SSL/TLS** - Email encryption with certifi

---

## 🚨 Important Notes

### Paystack Limits:

- **Test Mode**: No real money, test cards only
- **Live Mode**: Real money, real bank accounts
- **Transfer Limits**: Check Paystack dashboard for your limits
- **Verification**: Business verification may be required for higher limits

### Webhook Setup:

⚠️ **CRITICAL**: Webhooks will NOT work on localhost!

For testing webhooks locally:

1. Use **ngrok**: `ngrok http 8000`
2. Get public URL: `https://abc123.ngrok.io`
3. Set Paystack webhook: `https://abc123.ngrok.io/api/wallet/webhook/`

For production:

- Use your live domain: `https://yourdomain.com/api/wallet/webhook/`

### Withdrawal Processing Time:

- **Instant**: Wallet debited immediately
- **Bank Credit**: 5 minutes - 24 hours (Paystack processing)
- **Webhook**: You'll get confirmation when complete

---

## 📊 Monitoring & Logs

### Check Wallet Transactions:

```bash
GET /api/wallet/transactions/
# Returns all wallet transactions for user

GET /api/wallet/transactions/?transaction_type=CREDIT
# Filter by type: CREDIT, DEBIT, WITHDRAWAL, REFUND, etc.
```

### Check Withdrawal History:

```bash
GET /api/wallet/withdrawals/
# Returns all withdrawals

GET /api/wallet/withdrawals/?status=PROCESSING
# Filter by: PENDING, PROCESSING, SUCCESS, FAILED
```

### Django Logs:

```python
# Check logs/django.log for:
- "Wallet credited: user@email.com - ₦5,000.00"
- "Withdrawal initiated: user@email.com - ₦10,000.00"
- "Withdrawal completed: WITHDRAWAL_..."
```

### Celery Logs:

```python
# Check Celery terminal for:
- Email task queued
- Email sent successfully
- Any errors during email sending
```

---

## ✅ Final Checklist

### Before Going Live:

- [ ] Set `DEBUG=False` in production .env
- [ ] Configure `ALLOWED_HOSTS`
- [ ] Set up Paystack webhooks on live domain
- [ ] Test deposit with real money (small amount)
- [ ] Test withdrawal to real bank account
- [ ] Verify all emails arrive
- [ ] Check Celery worker is running
- [ ] Check Redis is running (Docker)
- [ ] Monitor logs for first few transactions
- [ ] Have support contact ready for users

### Development Mode:

- [x] Use `DEBUG=True` for local development
- [x] Test with Paystack test keys
- [x] Use ngrok for webhook testing
- [x] Run Celery worker locally
- [x] Run Redis in Docker

---

## 🎉 You're Ready for Production!

Your wallet system is **fully functional** and **production-ready**!

### What You Have:

1. ✅ Live Paystack integration (deposits + withdrawals)
2. ✅ Automated email notifications
3. ✅ Webhook handling for automatic crediting
4. ✅ Secure bank account verification
5. ✅ Tiered fee structure
6. ✅ Transaction history and reporting
7. ✅ Async processing with Celery
8. ✅ Error handling and refunds

### Next Steps:

1. Test with small amounts in production
2. Monitor first few transactions closely
3. Gather user feedback
4. Scale as needed

**Happy deploying! 🚀**
