# 🎯 Frontend Integration Plan

**Project:** Covu - Fashion Marketplace  
**Backend:** Django REST Framework (Fully Implemented)  
**Frontend:** HTML/CSS/JavaScript (Currently Mock Data)  
**Goal:** Connect frontend to backend API with JWT authentication

---

## 📊 Current Status

### ✅ Backend (100% Ready)

- **Authentication:** JWT tokens via `rest_framework_simplejwt`
- **Users API:** Registration, login, profile management
- **Stores API:** CRUD operations, product management
- **Products API:** List, search, filter, CRUD
- **Orders API:** Complete order lifecycle with escrow
- **Wallet API:** Paystack integration, transactions
- **Ratings API:** Store and product ratings
- **CORS:** Configured for localhost:5500, localhost:3000

### ❌ Frontend (0% Connected)

- **Current State:** All data stored in `localStorage`
- **Issue:** No API calls to Django backend
- **Data:** Hardcoded sample stores/products
- **Authentication:** Mock login (no JWT)
- **Orders:** Stored locally (not in database)

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     FRONTEND (Browser)                       │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   login.js   │  │ products.js  │  │  orders.js   │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                  │                  │               │
│         └──────────────────┼──────────────────┘              │
│                            │                                  │
│                    ┌───────▼────────┐                        │
│                    │    api.js      │  ◄─── Central API     │
│                    │  (API Handler) │       Manager          │
│                    └───────┬────────┘                        │
│                            │                                  │
└────────────────────────────┼──────────────────────────────────┘
                             │
                    ┌────────▼────────┐
                    │   HTTP/HTTPS    │
                    │   (with JWT)    │
                    └────────┬────────┘
                             │
┌────────────────────────────▼──────────────────────────────────┐
│                   BACKEND (Django)                             │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │  Users   │  │  Stores  │  │ Products │  │  Orders  │   │
│  │   API    │  │   API    │  │   API    │  │   API    │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
│                                                               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                  │
│  │  Wallet  │  │  Escrow  │  │ Ratings  │                  │
│  │   API    │  │   API    │  │   API    │                  │
│  └──────────┘  └──────────┘  └──────────┘                  │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎯 Integration Strategy

### **Phase 1: Foundation (Critical Path)**

**Goal:** Establish core API communication and authentication

1. **Create API Configuration Module**

   - `assets/js/config.js` - API base URL and settings
   - `assets/js/api.js` - Central API handler with JWT management
   - Error handling, token refresh, interceptors

2. **Authentication System**

   - Update `login.js` - Call Django `/api/users/login/`
   - Update `registration.js` - Call Django `/api/users/register/`
   - JWT token storage and management
   - Auto-redirect if not authenticated

3. **Custom JWT Response**
   - Backend: Create custom token serializer
   - Include user data in login response
   - Fix "undefined full_name" error

### **Phase 2: Core Features**

**Goal:** Connect main user-facing features

4. **Store Listing**

   - Update `script.js` (shop-list page)
   - Fetch stores from `/api/stores/`
   - Handle pagination, search, filters
   - Real ratings from backend

5. **Product Catalog**

   - Update `products.js`
   - Fetch products from `/api/stores/products/`
   - Search and filter functionality
   - Link to real stores

6. **User Profile**
   - Update `profile.js`
   - Fetch/update via `/api/users/profile/`
   - Real wallet balance
   - Shop activation (if seller)

### **Phase 3: Transactions**

**Goal:** Enable complete buying flow

7. **Order Creation**

   - Update `purchase.js`
   - Create orders via `/api/orders/`
   - Real-time wallet debit
   - Escrow holding confirmation

8. **Order Management**

   - Update `orders.js`
   - Fetch from `/api/orders/`
   - Order status updates (accept, deliver, confirm, cancel)
   - Real-time escrow release/refund

9. **Wallet Operations**
   - Keep Paystack integration
   - Fund wallet via `/api/wallet/fund/`
   - View transaction history

### **Phase 4: Enhanced Features**

**Goal:** Add seller features and social proof

10. **Seller Dashboard**

    - Update `shop.js`
    - Manage store via `/api/stores/{id}/`
    - Product CRUD operations
    - View orders received

11. **Product Details**

    - Update `product-detail.js`
    - Real product data
    - Rating and review system
    - Related products

12. **Seller Gallery**
    - Update `seller-gallery.js`
    - Display seller's products
    - Store ratings and reviews

---

## 🔐 Security Considerations

### **JWT Token Management**

```javascript
// Store tokens securely
localStorage.setItem('access_token', response.access);
localStorage.setItem('refresh_token', response.refresh);

// Include in all API requests
headers: {
    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
}

// Handle token expiration
if (response.status === 401) {
    // Try to refresh token
    // If refresh fails, redirect to login
}
```

### **API Error Handling**

- Network errors (offline mode)
- 400: Validation errors (show field errors)
- 401: Unauthorized (redirect to login)
- 403: Forbidden (show permission error)
- 404: Not found (show friendly message)
- 500: Server error (show generic error)

### **Data Validation**

- Client-side validation (UX)
- Server-side validation (security)
- Sanitize user inputs
- Handle edge cases

---

## 📊 Data Migration Strategy

### **What Happens to Current localStorage Data?**

**Option A: Clean Slate (Recommended)**

- Clear all localStorage on first backend connection
- Users re-register/login via API
- Start fresh with real backend data
- Cleanest approach, no conflicts

**Option B: Migration Script**

- Keep test users in localStorage temporarily
- Provide "migrate to server" button
- Copy localStorage orders to backend (if needed)
- More complex, potential conflicts

**Recommendation:** Option A - Clean slate, fresh start

---

## 🧪 Testing Strategy

### **Development Testing**

1. **API Endpoint Testing**

   - Use `api-tester.html` for manual testing
   - Test each endpoint before integrating
   - Verify request/response formats

2. **Feature Testing**

   - Test each page after integration
   - Verify data flows correctly
   - Check error handling

3. **Integration Testing**
   - Test complete user flows:
     - Registration → Login → Browse → Purchase → Order Tracking
     - Seller: Register → Create Store → Add Products → Receive Order

### **Browser Testing**

- Chrome (primary)
- Firefox
- Safari
- Edge
- Mobile browsers (responsive)

### **User Acceptance Testing**

- Test with real users
- Gather feedback
- Fix critical issues
- Optimize UX

---

## 🚀 Deployment Checklist

### **Backend Preparation**

- [ ] Set `DEBUG = False` in production
- [ ] Configure production `ALLOWED_HOSTS`
- [ ] Set production `CORS_ALLOWED_ORIGINS`
- [ ] Use environment variables for secrets
- [ ] Set up proper database (PostgreSQL recommended)
- [ ] Configure static files serving
- [ ] Set up Gunicorn/uWSGI
- [ ] Configure Nginx reverse proxy
- [ ] Enable HTTPS (SSL certificate)
- [ ] Set up Sentry for error tracking

### **Frontend Preparation**

- [ ] Update API base URL to production domain
- [ ] Minify JavaScript files
- [ ] Optimize images
- [ ] Test on production environment
- [ ] Set up CDN for static assets
- [ ] Configure caching headers

### **Third-Party Services**

- [ ] Switch Paystack to live keys
- [ ] Configure production email (Gmail SMTP or service)
- [ ] Set up production database backups
- [ ] Configure monitoring (UptimeRobot, etc.)

---

## 📈 Success Metrics

### **Functional Requirements**

- ✅ Users can register and login
- ✅ JWT authentication works
- ✅ Stores display from backend
- ✅ Products display from backend
- ✅ Orders can be created
- ✅ Wallet transactions work
- ✅ Escrow holds and releases funds
- ✅ Seller dashboard functional

### **Performance Requirements**

- API response time < 500ms
- Page load time < 3 seconds
- No console errors
- Smooth transitions
- Mobile responsive

### **User Experience**

- Intuitive navigation
- Clear error messages
- Loading states
- Success confirmations
- Consistent design

---

## 🛠️ Tools & Resources

### **Development Tools**

- **Browser DevTools:** Network tab for API debugging
- **Postman/Thunder Client:** API testing
- **VS Code Extensions:** REST Client, Live Server
- **Django Debug Toolbar:** Backend debugging

### **Documentation**

- Django REST Framework docs
- JWT documentation
- Paystack API docs
- JavaScript Fetch API

### **Code Quality**

- ESLint for JavaScript
- Prettier for formatting
- Console logging for debugging
- Git for version control

---

## 🎓 Learning Resources

### **For Team Members**

1. **REST API Basics**

   - HTTP methods (GET, POST, PUT, DELETE)
   - Status codes (200, 400, 401, 500)
   - Headers and authentication

2. **JWT Authentication**

   - What is JWT?
   - Access vs Refresh tokens
   - Token expiration handling

3. **Async JavaScript**

   - Promises
   - Async/await
   - Error handling with try/catch

4. **Django REST Framework**
   - Serializers
   - ViewSets
   - Permissions

---

## 📞 Support & Escalation

### **Common Issues & Solutions**

**Issue:** CORS errors

- **Solution:** Check `CORS_ALLOWED_ORIGINS` in `.env`
- Add frontend URL to allowed origins

**Issue:** 401 Unauthorized

- **Solution:** Check JWT token in request headers
- Verify token hasn't expired

**Issue:** 500 Server Error

- **Solution:** Check Django server logs
- Verify database migrations applied

**Issue:** Data not displaying

- **Solution:** Check API response in Network tab
- Verify data structure matches frontend expectations

---

## 🎯 Next Steps

1. **Read this plan** ✅ (You are here)
2. **Read FRONTEND-INTEGRATION-STEPS.md** for detailed instructions
3. **Read FRONTEND-INTEGRATION-PROGRESS.md** for task tracking
4. **Start implementation** following the steps

---

**Ready to proceed?** Let's build! 🚀
