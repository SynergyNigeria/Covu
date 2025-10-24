# 🔄 Infinite Scroll Implementation Guide

**Feature:** Progressive content loading as user scrolls  
**Replaces:** Traditional pagination  
**Benefits:** Better UX, seamless browsing, mobile-friendly

---

## 📋 Overview

Instead of pagination buttons (Previous/Next), content loads automatically when user scrolls near the bottom of the page.

### **How It Works:**

1. Load initial batch (20 items)
2. Monitor scroll position
3. When user scrolls within 200px of bottom, load next batch
4. Append new items to existing grid
5. Continue until no more items available

---

## 🔧 Configuration Updates

### **File: `frontend/assets/js/config.js`**

Update the configuration to include infinite scroll settings:

```javascript
const API_CONFIG = {
  // ... existing config ...

  // Infinite Scroll Settings
  PAGE_SIZE: 20, // Items per API call
  SCROLL_THRESHOLD: 200, // Pixels from bottom to trigger load
};
```

---

## 🏪 Store Listing (Shop List Page)

### **File: `frontend/assets/js/script.js`**

Add these variables and functions:

```javascript
// Infinite scroll state
let storesPage = 1;
let isLoadingStores = false;
let hasMoreStores = true;

// Load stores with infinite scroll support
async function loadStoresFromAPI(reset = false) {
  if (isLoadingStores || (!reset && !hasMoreStores)) {
    return; // Prevent duplicate requests
  }

  try {
    isLoadingStores = true;

    // Reset pagination if needed (e.g., after search/filter)
    if (reset) {
      storesPage = 1;
      hasMoreStores = true;
      stores.length = 0;
      storeGrid.innerHTML = "";
    }

    // Show loading indicator
    const loadingDiv = document.createElement("div");
    loadingDiv.id = "storesLoading";
    loadingDiv.className = "col-span-full text-center py-6";
    loadingDiv.innerHTML = `
            <div class="flex items-center justify-center gap-2">
                <div class="animate-spin h-5 w-5 border-2 border-primary-orange border-t-transparent rounded-full"></div>
                <span class="text-gray-500">Loading stores...</span>
            </div>
        `;
    storeGrid.appendChild(loadingDiv);

    // Fetch stores from API
    const response = await api.get(API_CONFIG.ENDPOINTS.STORES, {
      page: storesPage,
      page_size: API_CONFIG.PAGE_SIZE,
    });

    // Remove loading indicator
    const loading = document.getElementById("storesLoading");
    if (loading) loading.remove();

    // Add new stores to array
    stores.push(...response.results);

    // Display new stores (append to grid)
    response.results.forEach((store) => {
      const card = createStoreCard(store);
      storeGrid.appendChild(card);
    });

    // Re-initialize Lucide icons
    lucide.createIcons();

    // Update pagination state
    hasMoreStores = response.next !== null;
    storesPage++;

    // Show "no more stores" message if reached end
    if (!hasMoreStores && stores.length > 0) {
      const endDiv = document.createElement("div");
      endDiv.className = "col-span-full text-center py-6 text-gray-500 text-sm";
      endDiv.innerHTML = "✓ All stores loaded";
      storeGrid.appendChild(endDiv);
    }
  } catch (error) {
    console.error("Error loading stores:", error);

    // Remove loading indicator
    const loading = document.getElementById("storesLoading");
    if (loading) loading.remove();

    // Show error only if no stores loaded yet
    if (stores.length === 0) {
      storeGrid.innerHTML = `
                <div class="col-span-full text-center py-12">
                    <i data-lucide="alert-circle" class="h-12 w-12 text-red-500 mx-auto mb-4"></i>
                    <p class="text-red-500 mb-4">Failed to load stores</p>
                    <button onclick="loadStoresFromAPI(true)" class="bg-primary-orange text-white px-6 py-2 rounded-lg hover:bg-orange-600">
                        Retry
                    </button>
                </div>
            `;
      lucide.createIcons();
    } else {
      // Show inline error for subsequent loads
      const errorDiv = document.createElement("div");
      errorDiv.className = "col-span-full text-center py-4";
      errorDiv.innerHTML = `
                <p class="text-red-500 mb-2">Failed to load more stores</p>
                <button onclick="loadStoresFromAPI()" class="text-primary-orange underline">
                    Try again
                </button>
            `;
      storeGrid.appendChild(errorDiv);
    }
  } finally {
    isLoadingStores = false;
  }
}

// Initialize infinite scroll listener
function initStoresInfiniteScroll() {
  window.addEventListener("scroll", () => {
    // Calculate scroll position
    const scrollPosition = window.innerHeight + window.scrollY;
    const threshold =
      document.documentElement.scrollHeight - API_CONFIG.SCROLL_THRESHOLD;

    // Load more if near bottom and not already loading
    if (scrollPosition >= threshold && !isLoadingStores && hasMoreStores) {
      loadStoresFromAPI();
    }
  });
}

// Update search/filter functions to reset scroll
function filterStores() {
  const searchTerm = searchInput.value.toLowerCase();
  const activeCategories = getActiveCategories();

  // If searching/filtering, reload from start
  if (searchTerm || activeCategories.length > 0) {
    // TODO: Implement backend search/filter
    // For now, filter client-side
    const filteredStores = stores.filter((store) => {
      const matchesSearch = store.name.toLowerCase().includes(searchTerm);
      const matchesCategory =
        activeCategories.length === 0 ||
        store.categories.some((cat) => activeCategories.includes(cat));
      return matchesSearch && matchesCategory;
    });
    displayFilteredStores(filteredStores);
  } else {
    // No filters, reload all from API
    loadStoresFromAPI(true);
  }
}

// Initialize on page load
document.addEventListener("DOMContentLoaded", async () => {
  if (!api.requireAuth()) return;

  await loadStoresFromAPI();
  initStoresInfiniteScroll();
  lucide.createIcons();
  initStickySearch();
});
```

---

## 🛍️ Product Listing Page

### **File: `frontend/assets/js/products.js`**

Add these variables and functions:

```javascript
// Infinite scroll state
let productsPage = 1;
let isLoadingProducts = false;
let hasMoreProducts = true;
let currentFilters = {}; // Store active search/filters

// Load products with infinite scroll support
async function loadProductsFromAPI(reset = false) {
  if (isLoadingProducts || (!reset && !hasMoreProducts)) {
    return;
  }

  try {
    isLoadingProducts = true;

    // Reset pagination if needed
    if (reset) {
      productsPage = 1;
      hasMoreProducts = true;
      allProducts.length = 0;
      productGrid.innerHTML = "";
    }

    // Show loading indicator
    const loadingDiv = document.createElement("div");
    loadingDiv.id = "productsLoading";
    loadingDiv.className = "col-span-full text-center py-6";
    loadingDiv.innerHTML = `
            <div class="flex items-center justify-center gap-2">
                <div class="animate-spin h-5 w-5 border-2 border-primary-orange border-t-transparent rounded-full"></div>
                <span class="text-gray-500">Loading products...</span>
            </div>
        `;
    productGrid.appendChild(loadingDiv);

    // Build query params with filters
    const params = {
      page: productsPage,
      page_size: API_CONFIG.PAGE_SIZE,
      ...currentFilters,
    };

    // Fetch products from API
    const response = await api.get(API_CONFIG.ENDPOINTS.PRODUCTS, params);

    // Remove loading indicator
    const loading = document.getElementById("productsLoading");
    if (loading) loading.remove();

    // Add new products
    allProducts.push(...response.results);

    // Display new products (append to grid)
    response.results.forEach((product) => {
      const card = createProductCard(product);
      productGrid.appendChild(card);
    });

    // Re-initialize icons
    lucide.createIcons();

    // Update product count
    productCount.textContent = allProducts.length;

    // Update pagination state
    hasMoreProducts = response.next !== null;
    productsPage++;

    // Show "no more products" message
    if (!hasMoreProducts && allProducts.length > 0) {
      const endDiv = document.createElement("div");
      endDiv.className = "col-span-full text-center py-6 text-gray-500 text-sm";
      endDiv.innerHTML = "✓ All products loaded";
      productGrid.appendChild(endDiv);
    }
  } catch (error) {
    console.error("Error loading products:", error);

    const loading = document.getElementById("productsLoading");
    if (loading) loading.remove();

    if (allProducts.length === 0) {
      productGrid.innerHTML = `
                <div class="col-span-full text-center py-12">
                    <i data-lucide="alert-circle" class="h-12 w-12 text-red-500 mx-auto mb-4"></i>
                    <p class="text-red-500 mb-4">Failed to load products</p>
                    <button onclick="loadProductsFromAPI(true)" class="bg-primary-orange text-white px-6 py-2 rounded-lg">
                        Retry
                    </button>
                </div>
            `;
      lucide.createIcons();
    } else {
      const errorDiv = document.createElement("div");
      errorDiv.className = "col-span-full text-center py-4";
      errorDiv.innerHTML = `
                <p class="text-red-500 mb-2">Failed to load more products</p>
                <button onclick="loadProductsFromAPI()" class="text-primary-orange underline">
                    Try again
                </button>
            `;
      productGrid.appendChild(errorDiv);
    }
  } finally {
    isLoadingProducts = false;
  }
}

// Initialize infinite scroll
function initProductsInfiniteScroll() {
  window.addEventListener("scroll", () => {
    const scrollPosition = window.innerHeight + window.scrollY;
    const threshold =
      document.documentElement.scrollHeight - API_CONFIG.SCROLL_THRESHOLD;

    if (scrollPosition >= threshold && !isLoadingProducts && hasMoreProducts) {
      loadProductsFromAPI();
    }
  });
}

// Apply filters and reset scroll
function applyFilters(filters) {
  currentFilters = filters;
  loadProductsFromAPI(true); // Reset and reload with filters
}

// Update search function
searchInput.addEventListener("input", () => {
  const searchTerm = searchInput.value.trim();
  if (searchTerm) {
    applyFilters({ search: searchTerm });
  } else {
    applyFilters({});
  }
});

// Update category filter function
function toggleCategoryFilter(button, category) {
  // ... existing toggle logic ...

  // Get active categories
  const activeCategories = getActiveCategories();

  // Apply filter
  if (activeCategories.length > 0) {
    applyFilters({ category: activeCategories.join(",") });
  } else {
    applyFilters({});
  }
}

// Update sort function
sortSelect.addEventListener("change", () => {
  const sortValue = sortSelect.value;
  applyFilters({ ...currentFilters, ordering: sortValue });
});

// Initialize on page load
document.addEventListener("DOMContentLoaded", async () => {
  if (!api.requireAuth()) return;

  await loadProductsFromAPI();
  initProductsInfiniteScroll();
  populateCategories();
  lucide.createIcons();
  initStickySearch();
});
```

---

## 📦 Orders Page (Optional Infinite Scroll)

### **File: `frontend/assets/js/orders.js`**

For orders, infinite scroll is less critical (users typically have fewer orders), but can be implemented:

```javascript
let ordersPage = 1;
let isLoadingOrders = false;
let hasMoreOrders = true;

async function loadOrders(reset = false) {
  if (!api.requireAuth()) return;

  if (isLoadingOrders || (!reset && !hasMoreOrders)) {
    return;
  }

  try {
    isLoadingOrders = true;

    if (reset) {
      ordersPage = 1;
      hasMoreOrders = true;
      container.innerHTML = "";
    }

    // Show loading
    const loadingDiv = document.createElement("div");
    loadingDiv.id = "ordersLoading";
    loadingDiv.className = "text-center py-6";
    loadingDiv.innerHTML =
      '<div class="animate-pulse text-gray-500">Loading orders...</div>';
    container.appendChild(loadingDiv);

    // Fetch orders
    const response = await api.get(API_CONFIG.ENDPOINTS.ORDERS, {
      page: ordersPage,
      page_size: 10, // Smaller page size for orders
    });

    // Remove loading
    const loading = document.getElementById("ordersLoading");
    if (loading) loading.remove();

    const orders = response.results || [];

    if (orders.length === 0 && ordersPage === 1) {
      emptyState.classList.remove("hidden");
      return;
    }

    emptyState.classList.add("hidden");

    // Display orders
    orders.forEach((order) => {
      const orderCard = createOrderCard(order);
      container.appendChild(orderCard);
    });

    lucide.createIcons();

    hasMoreOrders = response.next !== null;
    ordersPage++;
  } catch (error) {
    console.error("Error loading orders:", error);

    const loading = document.getElementById("ordersLoading");
    if (loading) loading.remove();

    if (ordersPage === 1) {
      container.innerHTML = `
                <div class="text-center py-12">
                    <p class="text-red-500 mb-4">Failed to load orders</p>
                    <button onclick="loadOrders(true)" class="bg-primary-orange text-white px-6 py-2 rounded-lg">
                        Retry
                    </button>
                </div>
            `;
    }
  } finally {
    isLoadingOrders = false;
  }
}

// Optional: Add scroll listener for orders
function initOrdersInfiniteScroll() {
  window.addEventListener("scroll", () => {
    const scrollPosition = window.innerHeight + window.scrollY;
    const threshold = document.documentElement.scrollHeight - 200;

    if (scrollPosition >= threshold && !isLoadingOrders && hasMoreOrders) {
      loadOrders();
    }
  });
}
```

---

## 🎨 Loading Animation Styles

### **Add to your CSS:**

```css
/* Spinner animation */
@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.animate-spin {
  animation: spin 1s linear infinite;
}

/* Pulse animation for loading text */
@keyframes pulse {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

.animate-pulse {
  animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

/* Smooth scroll behavior */
html {
  scroll-behavior: smooth;
}
```

---

## ✅ Testing Checklist

### **Initial Load:**

- [ ] First 20 items load on page load
- [ ] Loading indicator displays briefly
- [ ] Items display correctly
- [ ] No console errors

### **Infinite Scroll:**

- [ ] Scrolling to bottom triggers next load
- [ ] Loading indicator shows during load
- [ ] New items append without flickering
- [ ] No duplicate items appear
- [ ] "All items loaded" message appears at end

### **Search/Filter:**

- [ ] Searching resets scroll to page 1
- [ ] Filter results load correctly
- [ ] Infinite scroll works with filtered results
- [ ] Clearing filters reloads all items

### **Error Handling:**

- [ ] Network error shows retry button
- [ ] Retry button works
- [ ] Error during scroll shows inline error
- [ ] Can continue scrolling after error fix

### **Edge Cases:**

- [ ] Works with slow network
- [ ] Works with fast scrolling
- [ ] Works on mobile devices
- [ ] Works with few items (< 20)
- [ ] Works with no items (empty state)

---

## 🐛 Common Issues & Solutions

### **Issue: Multiple duplicate requests**

**Solution:** Check `isLoading` flag is properly set/cleared

### **Issue: Scroll triggers too early/late**

**Solution:** Adjust `SCROLL_THRESHOLD` value (increase/decrease)

### **Issue: Items load but don't display**

**Solution:** Check `appendChild()` is used, not `innerHTML =`

### **Issue: Icons not showing on new items**

**Solution:** Call `lucide.createIcons()` after appending

### **Issue: Filters not working**

**Solution:** Ensure `reset=true` when applying filters

---

## 📊 Performance Tips

1. **Debounce scroll events** (prevent too frequent checks):

```javascript
let scrollTimeout;
window.addEventListener("scroll", () => {
  clearTimeout(scrollTimeout);
  scrollTimeout = setTimeout(checkScrollPosition, 100);
});
```

2. **Use CSS transforms** for smooth animations
3. **Lazy load images** with `loading="lazy"` attribute
4. **Limit DOM updates** - batch insertions when possible

---

## 🚀 Next Steps

1. Read this guide thoroughly
2. Implement infinite scroll during frontend integration
3. Test each page individually
4. Test with different network speeds
5. Test on mobile devices

**Ready to implement!** 🎉
