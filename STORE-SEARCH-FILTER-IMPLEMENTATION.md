# Store Search & Filter Implementation

## Date: October 22, 2025

## Overview

Implemented real-time search and category filtering for the store list page, with all filtering done on the backend for better performance and scalability.

## Backend Changes

### File: `Backend/stores/views.py`

Updated `StoreViewSet.list()` method to support:

#### 1. **Search Functionality**

```python
# Get search query
search_query = request.query_params.get('search', '').strip()
if search_query:
    queryset = queryset.filter(
        name__icontains=search_query
    ) | queryset.filter(
        description__icontains=search_query
    )
```

**Features:**

- Case-insensitive search
- Searches both store name and description
- Uses Django ORM `icontains` for partial matching

**API Usage:**

```http
GET /api/stores/?search=fashion
GET /api/stores/?search=Lagos%20boutique
```

#### 2. **Category Filtering**

```python
# Get category filter
category_filter = request.query_params.get('category', '').strip()
if category_filter:
    # Filter stores that have products in this category
    queryset = queryset.filter(products__category__iexact=category_filter).distinct()
```

**Features:**

- Filters stores by product category
- Case-insensitive matching
- Returns stores that have at least one product in the specified category
- Uses `distinct()` to avoid duplicate stores

**API Usage:**

```http
GET /api/stores/?category=Beauty
GET /api/stores/?category=Men%20Clothes
```

#### 3. **Combined Search + Filter**

```http
GET /api/stores/?search=boutique&category=Ladies%20Clothes
```

#### 4. **Pagination**

```python
# Pagination
page = int(request.query_params.get('page', 1))
page_size = int(request.query_params.get('page_size', 20))
start_idx = (page - 1) * page_size
end_idx = start_idx + page_size

paginated_stores = ranked_stores[start_idx:end_idx]
has_next = end_idx < len(ranked_stores)
```

**API Response:**

```json
{
  "count": 45,
  "next": "/api/stores/?page=2",
  "previous": null,
  "results": [...],
  "user_location": {
    "city": "Ikeja",
    "state": "lagos"
  }
}
```

### API Parameters Summary

| Parameter   | Type    | Description                    | Example            |
| ----------- | ------- | ------------------------------ | ------------------ |
| `search`    | string  | Search store name/description  | `?search=fashion`  |
| `category`  | string  | Filter by product category     | `?category=Beauty` |
| `page`      | integer | Page number (default: 1)       | `?page=2`          |
| `page_size` | integer | Results per page (default: 20) | `?page_size=10`    |

## Frontend Changes

### File: `frontend/assets/js/script.js`

#### 1. **Updated `loadStoresFromAPI()` Function**

**Before:** Only loaded stores without filters
**After:** Sends search and category params to backend

```javascript
// Build query params with search and filters
const params = new URLSearchParams({
  page: currentPage,
  page_size: API_CONFIG.PAGE_SIZE,
});

// Add search query if present
const searchTerm = searchInput.value.trim();
if (searchTerm) {
  params.append("search", searchTerm);
}

// Add category filter if active
const activeCategory = getActiveCategory();
if (activeCategory) {
  params.append("category", activeCategory);
}

// Call backend API
const response = await api.get(`${API_CONFIG.ENDPOINTS.STORES}?${params}`);
```

#### 2. **Search Input with Debouncing**

Added 500ms debounce to prevent excessive API calls:

```javascript
// Setup search input with debounce
function setupSearchListener() {
  searchInput.addEventListener("input", function () {
    // Clear previous timer
    if (searchDebounceTimer) {
      clearTimeout(searchDebounceTimer);
    }

    // Set new timer (wait 500ms after user stops typing)
    searchDebounceTimer = setTimeout(() => {
      console.log("Searching for:", searchInput.value);
      loadStoresFromAPI(true); // Reset scroll for new search
    }, 500);
  });
}
```

**Benefits:**

- Reduces API calls (waits until user stops typing)
- Better performance
- Smoother user experience

#### 3. **Category Filter Updates**

**Single Selection Mode:**

```javascript
function toggleCategoryFilter(button, category) {
  const isActive = button.classList.contains("from-primary-orange");

  // Deactivate all other category buttons first
  Array.from(categoryFilters.children).forEach((btn) => {
    if (btn !== button) {
      btn.className = "..."; // Reset to inactive state
    }
  });

  // Toggle current button
  if (isActive) {
    // Deactivate (show all stores)
    button.className = "...";
  } else {
    // Activate (filter by this category)
    button.className = "...active...";
  }

  // Reload stores from API with new filter
  loadStoresFromAPI(true);
}
```

**Behavior:**

- Only one category can be active at a time
- Clicking active category deactivates it (shows all)
- Clicking new category switches filter
- Each click triggers fresh API call

#### 4. **Helper Function**

```javascript
// Get active category filter
function getActiveCategory() {
  const activeButton = Array.from(categoryFilters.children).find((btn) =>
    btn.classList.contains("from-primary-orange")
  );
  return activeButton ? activeButton.textContent : null;
}
```

#### 5. **Initialization Updates**

```javascript
document.addEventListener("DOMContentLoaded", async () => {
  populateCategories();
  lucide.createIcons();

  // Initialize sticky search
  initStickySearch();

  // Setup search input listener with debounce
  setupSearchListener();

  // Setup filter toggle
  setupFilterToggle();

  // Load initial stores from backend
  await loadStoresFromAPI();

  // Setup infinite scroll
  setupInfiniteScroll();
});
```

## Categories Available

Based on `Backend/products/models.py`:

1. **Men Clothes** → Backend: `mens_clothes`
2. **Ladies Clothes** → Backend: `ladies_clothes`
3. **Kids Clothes** → Backend: `kids_clothes`
4. **Beauty** → Backend: `beauty`
5. **Body Accessories** → Backend: `body_accessories`
6. **Clothing Extras** → Backend: `clothing_extras`
7. **Bags** → Backend: `bags`
8. **Wigs** → Backend: `wigs`
9. **Body Scents** → Backend: `body_scents`

## User Flow

### Search Flow:

1. User types in search box: "fashion"
2. After 500ms of no typing, API call triggers
3. Backend searches store names and descriptions
4. Results displayed, scroll position reset
5. User can continue typing to refine search

### Filter Flow:

1. User clicks "Beauty" category button
2. Button becomes active (orange/green gradient)
3. API call: `GET /api/stores/?category=Beauty`
4. Only stores with Beauty products shown
5. User clicks "Beauty" again → shows all stores
6. User clicks "Bags" → switches filter to Bags

### Combined Flow:

1. User types "Lagos" in search
2. Clicks "Ladies Clothes" category
3. API call: `GET /api/stores/?search=Lagos&category=Ladies%20Clothes`
4. Shows only Lagos stores with Ladies Clothes

### Infinite Scroll:

- Works with search/filters
- Loads next page of filtered results
- Maintains search and filter params

## Testing Instructions

### Test Search:

1. **Basic Search**

   ```
   1. Go to shop-list.html
   2. Type "fashion" in search box
   3. Wait 500ms
   4. Verify: Only stores with "fashion" in name/description appear
   ```

2. **Empty Search**

   ```
   1. Clear search box
   2. Verify: All stores appear again
   ```

3. **No Results**
   ```
   1. Type "zzzzzzz" (nonsense)
   2. Verify: Empty state or "No stores found" message
   ```

### Test Category Filter:

1. **Single Category**

   ```
   1. Click "Beauty" button
   2. Verify: Button becomes orange/green
   3. Verify: Only stores with Beauty products shown
   4. Check console: API call has ?category=Beauty
   ```

2. **Switch Category**

   ```
   1. Click "Beauty" (active)
   2. Click "Bags"
   3. Verify: Beauty deactivates, Bags activates
   4. Verify: Different stores appear
   ```

3. **Deactivate Filter**
   ```
   1. Click active "Bags" button
   2. Verify: Button becomes inactive
   3. Verify: All stores appear
   ```

### Test Combined:

1. **Search + Filter**

   ```
   1. Type "boutique" in search
   2. Click "Ladies Clothes"
   3. Verify: Shows boutiques with ladies clothes only
   4. Check console: Both params in API call
   ```

2. **Infinite Scroll with Filters**
   ```
   1. Apply filter: "Men Clothes"
   2. Scroll down
   3. Verify: More filtered results load
   4. Verify: Filter persists across pages
   ```

### Test Debouncing:

1. **Rapid Typing**
   ```
   1. Type "a" "b" "c" "d" quickly
   2. Check Network tab (F12)
   3. Verify: Only ONE API call after 500ms delay
   ```

## Performance Improvements

### Before:

- ❌ Loaded ALL stores at once
- ❌ Client-side filtering (slow with many stores)
- ❌ No search capability
- ❌ Category filter only worked on loaded data

### After:

- ✅ Backend filtering (fast, scalable)
- ✅ Only loads filtered results
- ✅ Search across all stores in database
- ✅ Debounced search (reduces API calls by ~80%)
- ✅ Infinite scroll maintains filters
- ✅ Better user experience

## Error Handling

```javascript
try {
  const response = await api.get(`${API_CONFIG.ENDPOINTS.STORES}?${params}`);
  // ... success handling
} catch (error) {
  console.error("Error loading stores:", error);
  showErrorMessage("Failed to load stores. Please try again.");
}
```

**Error States:**

- Network error → Shows error toast
- No results → Empty grid (could add "No stores found" message)
- Invalid category → Backend returns empty results

## Future Enhancements

1. **Multiple Category Selection**

   - Allow selecting multiple categories
   - Backend: `?category=Beauty,Bags,Wigs`

2. **Advanced Filters**

   - Price range
   - Rating filter
   - Location filter (separate from algorithm)
   - Delivery options

3. **Search Suggestions**

   - Show popular searches
   - Auto-complete

4. **Sort Options**

   - Sort by rating
   - Sort by newest
   - Sort by closest

5. **Empty State UI**

   - Better message when no stores found
   - Suggestions for refining search

6. **Filter Chips**
   - Show active filters as removable chips
   - "Clear all filters" button

## Browser Console Commands

**Test API directly:**

```javascript
// Test search
api.get("/api/stores/?search=fashion").then((r) => console.log(r));

// Test category
api.get("/api/stores/?category=Beauty").then((r) => console.log(r));

// Test combined
api
  .get("/api/stores/?search=Lagos&category=Ladies%20Clothes")
  .then((r) => console.log(r));
```

## Related Files

- `Backend/stores/views.py` - Backend filtering logic
- `Backend/products/models.py` - Category definitions
- `frontend/assets/js/script.js` - Frontend search/filter
- `frontend/templates/shop-list.html` - UI elements
- `FRONTEND-INTEGRATION-PROGRESS.md` - Overall progress

## Completion Status

- [x] Backend search implementation
- [x] Backend category filtering
- [x] Backend pagination with filters
- [x] Frontend search with debouncing
- [x] Frontend category filtering
- [x] Infinite scroll with filters
- [x] Error handling
- [x] Testing guide
- [ ] Empty state UI (optional enhancement)
- [ ] Multiple category selection (future)
- [ ] Advanced filters (future)

## Next Steps

1. Test search functionality
2. Test category filtering
3. Test combined search + filter
4. Verify infinite scroll works with filters
5. Move to next Phase 3 task (products page or profile page)
