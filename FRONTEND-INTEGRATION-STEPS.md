# 📋 Frontend Integration - Detailed Steps

**Project:** Covu Fashion Marketplace  
**Phase:** Frontend-Backend Connection  
**Start Date:** October 22, 2025

---

## 🎯 Prerequisites

### **Before Starting:**

- ✅ Backend server running: `python manage.py runserver`
- ✅ Test users created: `buyer@test.com` / `seller@test.com` (password: `testpass123`)
- ✅ Test data: 1 store, 3 products in database
- ✅ CORS configured: `localhost:5500`, `localhost:3000`
- ✅ API documentation: `FRONTEND-API-GUIDE.md`

### **Required Knowledge:**

- JavaScript ES6+ (async/await, fetch API)
- HTML/CSS basics
- REST API concepts
- JWT authentication flow

---

## 🏗️ PHASE 1: FOUNDATION

### **STEP 1: Create API Configuration Module**

**Objective:** Central configuration for all API calls

**File:** `c:\Users\DELL\Desktop\frontend\assets\js\config.js`

```javascript
// API Configuration
const API_CONFIG = {
  // Base URL - Update for production
  BASE_URL: "http://localhost:8000/api",

  // Endpoints
  ENDPOINTS: {
    // Authentication
    LOGIN: "/users/login/",
    REGISTER: "/users/register/",
    REFRESH_TOKEN: "/users/token/refresh/",
    PROFILE: "/users/profile/",

    // Stores
    STORES: "/stores/",
    STORE_DETAIL: (id) => `/stores/${id}/`,
    STORE_PRODUCTS: (id) => `/stores/${id}/products/`,

    // Products
    PRODUCTS: "/stores/products/",
    PRODUCT_DETAIL: (id) => `/stores/products/${id}/`,

    // Orders
    ORDERS: "/orders/",
    ORDER_DETAIL: (id) => `/orders/${id}/`,
    ORDER_ACCEPT: (id) => `/orders/${id}/accept/`,
    ORDER_DELIVER: (id) => `/orders/${id}/deliver/`,
    ORDER_CONFIRM: (id) => `/orders/${id}/confirm/`,
    ORDER_CANCEL: (id) => `/orders/${id}/cancel/`,

    // Wallet
    WALLET_FUND: "/wallet/fund/",
    WALLET_VERIFY: "/wallet/verify-payment/",
    WALLET_TRANSACTIONS: "/wallet/transactions/",
    WALLET_WITHDRAW: "/wallet/withdraw/",

    // Ratings
    RATE_STORE: (id) => `/stores/${id}/rate/`,
    RATE_PRODUCT: (id) => `/stores/products/${id}/rate/`,
  },

  // Token keys for localStorage
  TOKEN_KEYS: {
    ACCESS: "access_token",
    REFRESH: "refresh_token",
    USER: "current_user",
  },

  // Request timeouts
  TIMEOUT: 30000, // 30 seconds

  // Pagination
  PAGE_SIZE: 20,
};

// Export for use in other files
if (typeof module !== "undefined" && module.exports) {
  module.exports = API_CONFIG;
}
```

**Action Items:**

- [ ] Create `config.js` file
- [ ] Copy configuration code
- [ ] Verify BASE_URL matches your Django server
- [ ] Test loading in browser console

---

### **STEP 2: Create Central API Handler**

**Objective:** Unified API request handler with JWT management

**File:** `c:\Users\DELL\Desktop\frontend\assets\js\api.js`

```javascript
// Central API Handler with Infinite Scroll Support
class APIHandler {
  constructor() {
    this.baseURL = API_CONFIG.BASE_URL;
    this.tokenKeys = API_CONFIG.TOKEN_KEYS;
  }

  // Get stored access token
  getAccessToken() {
    return localStorage.getItem(this.tokenKeys.ACCESS);
  }

  // Get stored refresh token
  getRefreshToken() {
    return localStorage.getItem(this.tokenKeys.REFRESH);
  }

  // Store tokens
  setTokens(accessToken, refreshToken) {
    localStorage.setItem(this.tokenKeys.ACCESS, accessToken);
    if (refreshToken) {
      localStorage.setItem(this.tokenKeys.REFRESH, refreshToken);
    }
  }

  // Clear tokens (logout)
  clearTokens() {
    localStorage.removeItem(this.tokenKeys.ACCESS);
    localStorage.removeItem(this.tokenKeys.REFRESH);
    localStorage.removeItem(this.tokenKeys.USER);
  }

  // Get stored user data
  getCurrentUser() {
    const userStr = localStorage.getItem(this.tokenKeys.USER);
    return userStr ? JSON.parse(userStr) : null;
  }

  // Store user data
  setCurrentUser(userData) {
    localStorage.setItem(this.tokenKeys.USER, JSON.stringify(userData));
  }

  // Build request headers
  buildHeaders(includeAuth = true, isFormData = false) {
    const headers = {};

    if (!isFormData) {
      headers["Content-Type"] = "application/json";
    }

    if (includeAuth) {
      const token = this.getAccessToken();
      if (token) {
        headers["Authorization"] = `Bearer ${token}`;
      }
    }

    return headers;
  }

  // Refresh access token
  async refreshAccessToken() {
    const refreshToken = this.getRefreshToken();

    if (!refreshToken) {
      throw new Error("No refresh token available");
    }

    try {
      const response = await fetch(
        `${this.baseURL}${API_CONFIG.ENDPOINTS.REFRESH_TOKEN}`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ refresh: refreshToken }),
        }
      );

      if (!response.ok) {
        throw new Error("Token refresh failed");
      }

      const data = await response.json();
      this.setTokens(data.access, null); // Only update access token
      return data.access;
    } catch (error) {
      // If refresh fails, clear tokens and redirect to login
      this.clearTokens();
      window.location.href = "/templates/login.html";
      throw error;
    }
  }

  // Main request method
  async request(endpoint, options = {}) {
    const {
      method = "GET",
      data = null,
      params = null,
      requiresAuth = true,
      isFormData = false,
      retryOnAuthFailure = true,
    } = options;

    // Build URL with query parameters
    let url = `${this.baseURL}${endpoint}`;
    if (params) {
      const queryString = new URLSearchParams(params).toString();
      url += `?${queryString}`;
    }

    // Build request config
    const config = {
      method,
      headers: this.buildHeaders(requiresAuth, isFormData),
    };

    // Add body for POST/PUT/PATCH
    if (data && ["POST", "PUT", "PATCH"].includes(method)) {
      config.body = isFormData ? data : JSON.stringify(data);
    }

    try {
      // Make the request
      const response = await fetch(url, config);

      // Handle 401 (Unauthorized) - Try to refresh token
      if (response.status === 401 && requiresAuth && retryOnAuthFailure) {
        await this.refreshAccessToken();
        // Retry the request with new token
        return this.request(endpoint, {
          ...options,
          retryOnAuthFailure: false,
        });
      }

      // Parse response
      const contentType = response.headers.get("content-type");
      let responseData = null;

      if (contentType && contentType.includes("application/json")) {
        responseData = await response.json();
      } else {
        responseData = await response.text();
      }

      // Handle non-OK responses
      if (!response.ok) {
        throw {
          status: response.status,
          message:
            responseData.detail || responseData.message || "Request failed",
          errors: responseData,
          response,
        };
      }

      return responseData;
    } catch (error) {
      console.error("API Request Error:", error);
      throw error;
    }
  }

  // Convenience methods
  async get(endpoint, params = null, requiresAuth = true) {
    return this.request(endpoint, { method: "GET", params, requiresAuth });
  }

  async post(endpoint, data, requiresAuth = true, isFormData = false) {
    return this.request(endpoint, {
      method: "POST",
      data,
      requiresAuth,
      isFormData,
    });
  }

  async put(endpoint, data, requiresAuth = true, isFormData = false) {
    return this.request(endpoint, {
      method: "PUT",
      data,
      requiresAuth,
      isFormData,
    });
  }

  async patch(endpoint, data, requiresAuth = true, isFormData = false) {
    return this.request(endpoint, {
      method: "PATCH",
      data,
      requiresAuth,
      isFormData,
    });
  }

  async delete(endpoint, requiresAuth = true) {
    return this.request(endpoint, { method: "DELETE", requiresAuth });
  }

  // Check if user is authenticated
  isAuthenticated() {
    return !!this.getAccessToken();
  }

  // Redirect to login if not authenticated
  requireAuth(redirectUrl = "/templates/login.html") {
    if (!this.isAuthenticated()) {
      window.location.href = redirectUrl;
      return false;
    }
    return true;
  }
}

// Create global API instance
const api = new APIHandler();

// Export for use in other files
if (typeof module !== "undefined" && module.exports) {
  module.exports = { APIHandler, api };
}
```

**Action Items:**

- [ ] Create `api.js` file
- [ ] Copy API handler code
- [ ] Test in browser console: `api.isAuthenticated()`
- [ ] Verify token storage works

---

### **STEP 3: Fix Backend JWT Response**

**Objective:** Include user data in JWT login response

**File:** `c:\Users\DELL\Desktop\Backend\users\serializers.py`

```python
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers
from .models import CustomUser

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Custom JWT serializer that includes user data in response"""

    def validate(self, attrs):
        # Get the default token response
        data = super().validate(attrs)

        # Add user data to response
        data['user'] = {
            'id': str(self.user.id),
            'email': self.user.email,
            'full_name': self.user.full_name,
            'phone_number': self.user.phone_number,
            'state': self.user.state,
            'city': self.user.city,
            'is_seller': self.user.is_seller,
            'wallet_balance': float(self.user.wallet_balance),
            'is_active': self.user.is_active,
        }

        return data
```

**File:** `c:\Users\DELL\Desktop\Backend\users\views.py`

Add at the top:

```python
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import CustomTokenObtainPairSerializer

class CustomTokenObtainPairView(TokenObtainPairView):
    """Custom token view that uses our custom serializer"""
    serializer_class = CustomTokenObtainPairSerializer
```

**File:** `c:\Users\DELL\Desktop\Backend\users\urls.py`

Update the login path:

```python
from .views import CustomTokenObtainPairView

urlpatterns = [
    path("register/", UserRegistrationView.as_view(), name="register"),
    path("login/", CustomTokenObtainPairView.as_view(), name="login"),  # Updated
    # ... rest of urls
]
```

**Action Items:**

- [ ] Update `serializers.py`
- [ ] Update `views.py`
- [ ] Update `urls.py`
- [ ] Restart Django server
- [ ] Test login endpoint with `api-tester.html`

---

### **STEP 4: Update Login Page**

**Objective:** Connect login to Django API

**File:** `c:\Users\DELL\Desktop\frontend\templates\login.html`

Update the `<head>` section to include new scripts:

```html
<!-- Add before closing </head> -->
<script src="/assets/js/config.js"></script>
<script src="/assets/js/api.js"></script>
```

**File:** `c:\Users\DELL\Desktop\frontend\assets\js\login.js`

Replace the `handleLogin()` function:

```javascript
// Login handler
async function handleLogin() {
  const email = emailInput.value.trim().toLowerCase();
  const password = passwordInput.value;
  const rememberMe = rememberMeCheckbox.checked;

  // Validation
  let errors = [];

  if (!email) {
    errors.push("Email is required");
  } else if (!validateEmail(email)) {
    errors.push("Please enter a valid email address");
  }

  if (!password) {
    errors.push("Password is required");
  }

  if (errors.length > 0) {
    showToast(errors[0], "error");
    return;
  }

  // Disable submit button
  submitBtn.disabled = true;
  submitBtn.querySelector("span").textContent = "Signing in...";

  try {
    // Call API
    const response = await api.post(
      API_CONFIG.ENDPOINTS.LOGIN,
      {
        email: email,
        password: password,
      },
      false
    ); // false = no auth required for login

    // Store tokens and user data
    api.setTokens(response.access, response.refresh);
    api.setCurrentUser(response.user);

    // Handle remember me
    if (rememberMe) {
      localStorage.setItem("rememberedEmail", email);
    } else {
      localStorage.removeItem("rememberedEmail");
    }

    // Success message
    showToast(`Welcome back, ${response.user.full_name}!`, "success");

    // Redirect to shop list
    setTimeout(() => {
      window.location.href = "shop-list.html";
    }, 1500);
  } catch (error) {
    console.error("Login error:", error);

    let errorMessage = "Login failed. Please try again.";

    if (error.status === 401) {
      errorMessage = "Invalid email or password";
    } else if (error.message) {
      errorMessage = error.message;
    }

    showToast(errorMessage, "error");

    // Re-enable submit button
    submitBtn.disabled = false;
    submitBtn.querySelector("span").textContent = "Sign In";
  }
}
```

**Action Items:**

- [ ] Update login.html to include scripts
- [ ] Replace handleLogin() function in login.js
- [ ] Test login with: `buyer@test.com` / `testpass123`
- [ ] Verify tokens stored in localStorage
- [ ] Check redirect to shop-list works

---

### **STEP 5: Update Registration Page**

**Objective:** Connect registration to Django API

**File:** `c:\Users\DELL\Desktop\frontend\templates\register.html`

Update the `<head>` section:

```html
<!-- Add before closing </head> -->
<script src="/assets/js/config.js"></script>
<script src="/assets/js/api.js"></script>
```

**File:** `c:\Users\DELL\Desktop\frontend\assets\js\registration.js`

Replace the `handleRegistration()` function:

```javascript
// Registration handler
async function handleRegistration() {
  const formData = new FormData(registrationForm);
  const userData = {
    full_name: formData.get("fullName").trim(),
    email: formData.get("email").trim().toLowerCase(),
    phone_number: formData.get("phone").replace(/\s/g, ""), // Remove spaces
    state: formData.get("state"),
    city: formData.get("lga"), // Backend uses 'city' field
    password: formData.get("password"),
    confirmPassword: formData.get("confirmPassword"),
    terms: formData.get("terms") === "on",
  };

  // Client-side validation
  let errors = [];

  if (!userData.full_name || userData.full_name.length < 2) {
    errors.push("Full name must be at least 2 characters long");
  }

  if (!validateEmail(userData.email)) {
    errors.push("Please enter a valid email address");
  }

  if (!validatePhone(userData.phone_number)) {
    errors.push("Please enter a valid Nigerian phone number");
  }

  if (!userData.state) {
    errors.push("Please select your state");
  }

  if (!userData.city) {
    errors.push("Please select your Local Government Area (LGA)");
  }

  if (userData.password.length < 8) {
    errors.push("Password must be at least 8 characters long");
  }

  if (userData.password !== userData.confirmPassword) {
    errors.push("Passwords do not match");
  }

  if (!userData.terms) {
    errors.push("You must agree to the Terms of Service and Privacy Policy");
  }

  if (errors.length > 0) {
    showToast(errors[0], "error");
    return;
  }

  // Disable submit button
  submitBtn.disabled = true;
  submitBtn.querySelector("span").textContent = "Creating Account...";

  try {
    // Call API
    const response = await api.post(
      API_CONFIG.ENDPOINTS.REGISTER,
      {
        email: userData.email,
        password: userData.password,
        full_name: userData.full_name,
        phone_number: userData.phone_number,
        state: userData.state,
        city: userData.city,
      },
      false
    ); // false = no auth required for registration

    // Success message
    showToast("Account created successfully! Please log in.", "success");

    // Redirect to login after delay
    setTimeout(() => {
      window.location.href = "login.html";
    }, 2000);
  } catch (error) {
    console.error("Registration error:", error);

    let errorMessage = "Registration failed. Please try again.";

    if (error.errors) {
      // Show first validation error
      const firstError = Object.values(error.errors)[0];
      if (Array.isArray(firstError)) {
        errorMessage = firstError[0];
      } else {
        errorMessage = firstError;
      }
    } else if (error.message) {
      errorMessage = error.message;
    }

    showToast(errorMessage, "error");

    // Re-enable submit button
    submitBtn.disabled = false;
    submitBtn.querySelector("span").textContent = "Create Account";
  }
}
```

**Action Items:**

- [ ] Update register.html to include scripts
- [ ] Replace handleRegistration() function
- [ ] Test registration with new user
- [ ] Verify redirect to login
- [ ] Test login with newly registered user

---

## 🏗️ PHASE 2: CORE FEATURES

### **STEP 6: Update Store Listing (Shop List)**

**Objective:** Display real stores from backend

**File:** `c:\Users\DELL\Desktop\frontend\templates\shop-list.html`

Update `<head>`:

```html
<script src="/assets/js/config.js"></script>
<script src="/assets/js/api.js"></script>
```

**File:** `c:\Users\DELL\Desktop\frontend\assets\js/script.js`

Add at the top:

```javascript
// Check authentication
document.addEventListener("DOMContentLoaded", async () => {
  // Require authentication (redirect to login if not authenticated)
  if (!api.requireAuth()) {
    return;
  }

  // Load stores from API
  await loadStoresFromAPI();

  // Initialize the rest
  lucide.createIcons();
  initStickySearch();
});

// Load stores from Django backend
async function loadStoresFromAPI() {
  try {
    // Show loading state
    storeGrid.innerHTML =
      '<div class="col-span-full text-center py-12">Loading stores...</div>';

    // Fetch stores from API
    const response = await api.get(API_CONFIG.ENDPOINTS.STORES);

    // Update global stores variable
    stores.length = 0; // Clear array
    stores.push(...response.results); // Add new stores

    // Display stores
    displayStores(stores);
  } catch (error) {
    console.error("Error loading stores:", error);
    storeGrid.innerHTML = `
            <div class="col-span-full text-center py-12">
                <p class="text-red-500 mb-4">Failed to load stores</p>
                <button onclick="loadStoresFromAPI()" class="bg-primary-orange text-white px-6 py-2 rounded-lg">
                    Retry
                </button>
            </div>
        `;
  }
}
```

Update `createStoreCard()` function to match API response format:

```javascript
function createStoreCard(store) {
  const card = document.createElement("div");
  card.className =
    "bg-white rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-shadow duration-300 cursor-pointer";
  card.addEventListener("click", () => openStoreModal(store));

  // Use store.logo for image, fallback to placeholder
  const imageUrl =
    store.logo ||
    "https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=400&h=300&fit=crop";

  // Use store.average_rating from backend
  const rating = store.average_rating || 0;
  const stars = createStars(rating);

  card.innerHTML = `
        <img src="${imageUrl}" alt="${
    store.name
  }" class="w-full h-48 object-cover" loading="lazy">
        <div class="p-4">
            <h3 class="text-lg font-semibold text-gray-800">${store.name}</h3>
            <p class="text-gray-600 text-sm mb-2">${
              store.description || "No description"
            }</p>
            <div class="flex items-center mb-2">
                <div class="flex text-yellow-400">
                    ${stars}
                </div>
                <span class="ml-2 text-sm text-gray-600">${rating.toFixed(
                  1
                )}</span>
            </div>
            <div class="flex items-center text-sm text-gray-500 mb-4">
                <i data-lucide="map-pin" class="h-4 w-4 mr-1"></i>
                ${store.state}, Nigeria
            </div>
            <button class="w-full bg-primary-orange text-white py-2 rounded-lg hover:bg-orange-600 transition-colors" onclick="event.stopPropagation(); openStoreModal('${
              store.id
            }')">View Store</button>
        </div>
    `;

  return card;
}
```

**Action Items:**

- [ ] Update shop-list.html to include scripts
- [ ] Add loadStoresFromAPI() function
- [ ] Update createStoreCard() to match API format
- [ ] Test store loading
- [ ] Verify search and filters still work

---

### **STEP 7: Update Product Listing**

**Objective:** Display real products from backend

**File:** `c:\Users\DELL\Desktop\frontend\templates\products.html`

Update `<head>`:

```html
<script src="/assets/js/config.js"></script>
<script src="/assets/js/api.js"></script>
```

**File:** `c:\Users\DELL\Desktop\frontend\assets\js\products.js`

Replace initialization:

```javascript
document.addEventListener("DOMContentLoaded", async () => {
  // Require authentication
  if (!api.requireAuth()) {
    return;
  }

  // Load products from API
  await loadProductsFromAPI();

  populateCategories();
  lucide.createIcons();
  initStickySearch();
});

// Load products from Django backend
async function loadProductsFromAPI() {
  try {
    // Show loading state
    productGrid.innerHTML =
      '<div class="col-span-full text-center py-12">Loading products...</div>';

    // Fetch products from API
    const response = await api.get(API_CONFIG.ENDPOINTS.PRODUCTS);

    // Update global products variable
    allProducts.length = 0;
    allProducts.push(...response.results);

    // Display products
    displayProducts(allProducts);
  } catch (error) {
    console.error("Error loading products:", error);
    productGrid.innerHTML = `
            <div class="col-span-full text-center py-12">
                <p class="text-red-500 mb-4">Failed to load products</p>
                <button onclick="loadProductsFromAPI()" class="bg-primary-orange text-white px-6 py-2 rounded-lg">
                    Retry
                </button>
            </div>
        `;
  }
}
```

Update `createProductCard()`:

```javascript
function createProductCard(product) {
  const card = document.createElement("div");
  card.className =
    "bg-white rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-shadow duration-300 cursor-pointer";
  card.addEventListener("click", () => openProductModal(product));

  // Use product.images[0] if available
  const imageUrl =
    product.images && product.images.length > 0
      ? product.images[0].image
      : "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=300&h=300&fit=crop";

  card.innerHTML = `
        <img src="${imageUrl}" alt="${
    product.name
  }" class="w-full h-40 object-cover" loading="lazy">
        <div class="p-3">
            <h3 class="text-sm font-semibold text-gray-800 mb-1 line-clamp-2">${
              product.name
            }</h3>
            <p class="text-primary-orange font-bold text-lg mb-1">₦${parseFloat(
              product.price
            ).toLocaleString()}</p>
            <div class="flex items-center text-xs text-gray-500 mb-2">
                <i data-lucide="store" class="h-3 w-3 mr-1"></i>
                ${product.store_name || "Store"}
            </div>
            ${
              product.stock_quantity === 0
                ? '<p class="text-red-500 text-xs font-medium">Out of Stock</p>'
                : ""
            }
        </div>
    `;

  return card;
}
```

**Action Items:**

- [ ] Update products.html to include scripts
- [ ] Add loadProductsFromAPI() function
- [ ] Update createProductCard() to match API format
- [ ] Test product loading
- [ ] Verify filters and search work

---

### **STEP 8: Update User Profile**

**Objective:** Load/update profile from backend

**File:** `c:\Users\DELL\Desktop\frontend\templates\profile.html`

Update `<head>`:

```html
<script src="/assets/js/config.js"></script>
<script src="/assets/js/api.js"></script>
```

**File:** `c:\Users\DELL\Desktop\frontend\assets\js\profile.js`

Replace `loadUserProfile()`:

```javascript
async function loadUserProfile() {
  // Check authentication
  if (!api.requireAuth()) {
    return;
  }

  try {
    // Get user data from token storage (set during login)
    const userData = api.getCurrentUser();

    if (userData) {
      // Populate form fields
      document.getElementById("userName").textContent = userData.full_name;
      document.getElementById("userEmail").textContent = userData.email;
      document.getElementById("userPhone").textContent = userData.phone_number;
      document.getElementById("state").value = userData.state || "";
      document.getElementById("city").value = userData.city || "";
      document.getElementById("contactEmail").value = userData.email;
      document.getElementById("contactPhone").value = userData.phone_number;

      // Update shop status
      updateShopStatus(userData.is_seller, userData.shop_name || "");

      // Display wallet balance
      document.getElementById("walletBalance").textContent = `₦${parseFloat(
        userData.wallet_balance
      ).toLocaleString()}`;
    }
  } catch (error) {
    console.error("Error loading profile:", error);
    showToast("Failed to load profile", "error");
  }
}
```

Add logout function:

```javascript
function handleLogout() {
  if (confirm("Are you sure you want to log out?")) {
    // Clear tokens
    api.clearTokens();

    showToast("Logged out successfully!", "success");

    // Redirect to login
    setTimeout(() => {
      window.location.href = "login.html";
    }, 1000);
  }
}
```

**Action Items:**

- [ ] Update profile.html to include scripts
- [ ] Replace loadUserProfile() function
- [ ] Update handleLogout() function
- [ ] Test profile page loads
- [ ] Verify wallet balance displays

---

## 🏗️ PHASE 3: TRANSACTIONS

### **STEP 9: Update Order Creation (Purchase)**

**Objective:** Create orders via backend API

**File:** `c:\Users\DELL\Desktop\frontend\templates\purchase.html`

Update `<head>`:

```html
<script src="/assets/js/config.js"></script>
<script src="/assets/js/api.js"></script>
```

**File:** `c:\Users\DELL\Desktop\frontend\assets\js\purchase.js`

Replace `processPurchase()`:

```javascript
async function processPurchase(
  paymentAmount,
  productData,
  loadingState,
  successState,
  orderIdElement
) {
  try {
    // Create order via API
    const orderData = {
      product: productData.id,
      delivery_address: "User delivery address", // TODO: Get from user profile or form
      quantity: 1,
    };

    const response = await api.post(API_CONFIG.ENDPOINTS.ORDERS, orderData);

    // Update user balance in storage
    const currentUser = api.getCurrentUser();
    currentUser.wallet_balance =
      parseFloat(currentUser.wallet_balance) - paymentAmount;
    api.setCurrentUser(currentUser);

    // Update wallet balance display
    document.getElementById("walletBalance").textContent = formatCurrency(
      currentUser.wallet_balance
    );

    // Show success state
    loadingState.classList.add("hidden");
    successState.classList.remove("hidden");
    orderIdElement.textContent = response.id;

    // Animate success
    const successTick = document.getElementById("successTick");
    successTick.classList.add("animate-pulse");

    // Clear selected product
    localStorage.removeItem("selectedProduct");

    // Show toast
    showToast("Payment successful! Order has been placed.", "success");
  } catch (error) {
    console.error("Order creation error:", error);

    let errorMessage = "Failed to create order. Please try again.";
    if (error.message) {
      errorMessage = error.message;
    }

    // Hide modal and show error
    document.getElementById("purchaseModal").classList.add("hidden");
    alert(errorMessage);
  }
}
```

**Action Items:**

- [ ] Update purchase.html to include scripts
- [ ] Replace processPurchase() function
- [ ] Add delivery address input field
- [ ] Test order creation
- [ ] Verify wallet debit works

---

### **STEP 10: Update Order Management**

**Objective:** Display and manage orders from backend

**File:** `c:\Users\DELL\Desktop\frontend\templates\orders.html`

Update `<head>`:

```html
<script src="/assets/js/config.js"></script>
<script src="/assets/js/api.js"></script>
```

**File:** `c:\Users\DELL\Desktop\frontend\assets\js\orders.js`

Replace `loadOrders()`:

```javascript
async function loadOrders() {
  // Check authentication
  if (!api.requireAuth()) {
    return;
  }

  try {
    // Fetch orders from API
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

Replace `handleOrderAction()`:

```javascript
async function handleOrderAction(orderId, action) {
  if (!confirm(`Are you sure you want to ${action} this order?`)) {
    return;
  }

  try {
    let endpoint;

    switch (action) {
      case "cancel":
        endpoint = API_CONFIG.ENDPOINTS.ORDER_CANCEL(orderId);
        break;
      case "deliver":
        endpoint = API_CONFIG.ENDPOINTS.ORDER_CONFIRM(orderId);
        break;
      default:
        throw new Error("Invalid action");
    }

    // Call API
    await api.post(endpoint, {});

    // Show success message
    showMessage(`Order ${action}ed successfully`, "success");

    // Reload orders
    await loadOrders();
  } catch (error) {
    console.error("Order action error:", error);
    showMessage(error.message || "Action failed", "error");
  }
}
```

Update `getStatusInfo()` to match backend statuses:

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
      description: "Order delivered, awaiting confirmation",
      button: {
        text: "Confirm Receipt",
        action: "deliver",
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

**Action Items:**

- [ ] Update orders.html to include scripts
- [ ] Replace loadOrders() function
- [ ] Replace handleOrderAction() function
- [ ] Update getStatusInfo() for backend statuses
- [ ] Test order display and actions

---

## 🎯 Testing & Validation

### **Test Scenarios**

**Authentication Flow:**

1. Register new user → Should redirect to login
2. Login with credentials → Should redirect to shop-list
3. Access protected page without login → Should redirect to login
4. Logout → Should clear tokens and redirect to login

**Store & Products:**

1. View stores list → Should display real stores from backend
2. Search stores → Should filter correctly
3. View products → Should display real products
4. Filter products by category → Should work

**Order Flow:**

1. Select product → View purchase page
2. Create order → Should debit wallet, create order
3. View orders → Should display backend orders
4. Cancel order → Should refund wallet
5. Confirm delivery → Should release escrow

**Error Handling:**

1. Network error → Should show retry button
2. 401 Unauthorized → Should refresh token or redirect to login
3. Validation error → Should show specific error message
4. Server error → Should show generic error message

---

## 🚀 Deployment Preparation

### **Production Checklist**

**Backend:**

- [ ] Set `DEBUG = False`
- [ ] Update `ALLOWED_HOSTS`
- [ ] Update `CORS_ALLOWED_ORIGINS` with production frontend URL
- [ ] Use environment variables for all secrets
- [ ] Switch Paystack to live keys
- [ ] Set up production database
- [ ] Configure Gunicorn/uWSGI
- [ ] Set up Nginx
- [ ] Enable HTTPS

**Frontend:**

- [ ] Update `config.js` BASE_URL to production API
- [ ] Minify JavaScript files
- [ ] Optimize images
- [ ] Test on production environment
- [ ] Set up CDN for static assets

---

## 📞 Support

**Common Issues:**

1. **CORS Error:** Update `.env` CORS_ALLOWED_ORIGINS
2. **401 Errors:** Check JWT token in localStorage
3. **500 Errors:** Check Django server logs
4. **Data not displaying:** Check Network tab in DevTools

**Need Help?**

- Check browser console for errors
- Check Django server terminal for errors
- Review API documentation: `FRONTEND-API-GUIDE.md`
- Test endpoints with: `api-tester.html`

---

**Next:** Read `FRONTEND-INTEGRATION-PROGRESS.md` to track implementation progress! 🎉
