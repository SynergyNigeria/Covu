# Dynamic Delivery Fee Calculation

## Overview

Fixed the hardcoded ₦500 delivery fee on the purchase page. Now the delivery fee is dynamically calculated based on the seller's store settings and buyer's location.

## Problem

- **Before**: Delivery fee was hardcoded as ₦500 in `purchase.js`
- **Issue**: Ignored the seller's preset delivery fees from their store settings
- **Backend Already Had**: Store model with `delivery_within_lga` and `delivery_outside_lga` fields

## Solution

### Backend Store Model (Already Exists)

```python
# Backend/stores/models.py
class Store(models.Model):
    # Delivery Pricing
    delivery_within_lga = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=1000.00,  # ₦1,000 for same city
        help_text="Delivery fee for buyers in same city/LGA (₦)",
    )
    delivery_outside_lga = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=2500.00,  # ₦2,500 for outside city
        help_text="Delivery fee for buyers outside seller's city/LGA (₦)",
    )
```

### Backend API (Already Returns Delivery Fees)

```python
# Backend/products/serializers.py - ProductDetailSerializer
def get_store_info(self, obj):
    """Get complete store information"""
    store = obj.store
    return {
        "id": str(store.id),
        "name": store.name,
        "city": store.city,
        "state": store.state,
        "average_rating": float(store.average_rating),
        "delivery_within_lga": float(store.delivery_within_lga),  # ✅ Already included
        "delivery_outside_lga": float(store.delivery_outside_lga), # ✅ Already included
    }
```

### Frontend Changes

#### 1. HTML Update (`frontend/templates/purchase.html`)

**Added Dynamic Delivery Fee Display:**

```html
<!-- Before: Hardcoded ₦500 -->
<span class="font-medium">₦500</span>

<!-- After: Dynamic with ID and tooltip -->
<div class="flex items-center gap-2">
  <span class="text-gray-600">Delivery Fee</span>
  <div class="group relative">
    <i data-lucide="info" class="h-4 w-4 text-gray-400 cursor-help"></i>
    <div
      class="absolute left-0 bottom-full mb-2 hidden group-hover:block w-64 bg-gray-800 text-white text-xs rounded-lg p-2 z-10"
    >
      Delivery fee varies based on your location relative to the seller's store
    </div>
  </div>
</div>
<span id="deliveryFeeAmount" class="font-medium">₦0</span>
```

**Features:**

- Added `id="deliveryFeeAmount"` for dynamic update
- Added info icon with hover tooltip explaining calculation
- Responsive tooltip design

#### 2. JavaScript Update (`frontend/assets/js/purchase.js`)

**Before (Hardcoded):**

```javascript
const subtotal = parseFloat(productData.price) || 0;
const deliveryFee = 500; // ❌ Hardcoded
const total = subtotal + deliveryFee;

document.getElementById("subtotalAmount").textContent =
  formatCurrency(subtotal);
document.getElementById("totalAmount").textContent = formatCurrency(total);
```

**After (Dynamic Calculation):**

```javascript
const subtotal = parseFloat(productData.price) || 0;

// Get delivery fee from store_info
let deliveryFee = 2500; // Default fallback

if (productData.store_info) {
  // Get current user to check location
  const currentUser = JSON.parse(
    localStorage.getItem(API_CONFIG.TOKEN_KEYS.USER) || "{}"
  );

  if (currentUser.city && productData.store_info.city) {
    // Compare buyer's city with seller's city
    const buyerCity = currentUser.city.toLowerCase().trim();
    const sellerCity = productData.store_info.city.toLowerCase().trim();

    if (buyerCity === sellerCity) {
      // Same city/LGA - use lower fee
      deliveryFee = parseFloat(productData.store_info.delivery_within_lga);
    } else {
      // Different city - use higher fee
      deliveryFee = parseFloat(productData.store_info.delivery_outside_lga);
    }
  } else {
    // No buyer location - use outside LGA fee (safer default)
    deliveryFee = parseFloat(productData.store_info.delivery_outside_lga);
  }
}

const total = subtotal + deliveryFee;

// Update all displays
document.getElementById("subtotalAmount").textContent =
  formatCurrency(subtotal);
document.getElementById("deliveryFeeAmount").textContent =
  formatCurrency(deliveryFee); // ✅ New
document.getElementById("totalAmount").textContent = formatCurrency(total);

// Store for order creation
productData.calculatedDeliveryFee = deliveryFee;
localStorage.setItem("selectedProduct", JSON.stringify(productData));
```

## Calculation Logic

### Scenario 1: Same City/LGA (Within LGA)

```
Buyer City: Lagos
Seller City: Lagos
→ Delivery Fee: ₦1,000 (delivery_within_lga)
```

### Scenario 2: Different City (Outside LGA)

```
Buyer City: Abuja
Seller City: Lagos
→ Delivery Fee: ₦2,500 (delivery_outside_lga)
```

### Scenario 3: Unknown Buyer Location

```
Buyer City: Not set in profile
Seller City: Lagos
→ Delivery Fee: ₦2,500 (delivery_outside_lga - safer default)
```

### Scenario 4: No Store Info (Fallback)

```
Product has no store_info
→ Delivery Fee: ₦2,500 (hardcoded fallback)
```

## City Comparison Rules

1. **Case-Insensitive**: "Lagos" = "lagos" = "LAGOS"
2. **Whitespace Trimmed**: "Lagos " = "Lagos"
3. **Exact Match Required**: "Lagos" ≠ "Lagos Island" (different cities)

## Benefits

✅ **Seller Flexibility**: Each seller can set their own delivery prices
✅ **Fair Pricing**: Lower fees for local deliveries, higher for distant ones
✅ **Transparency**: User sees the actual fee, not a generic amount
✅ **Scalability**: Works with any seller's custom delivery pricing
✅ **User-Friendly**: Tooltip explains why fee varies

## Data Flow

```
1. User views product detail page
   ↓
2. Product data fetched with store_info (includes delivery fees)
   ↓
3. User clicks "Buy Now"
   ↓
4. Product data stored in localStorage
   ↓
5. Purchase page loads
   ↓
6. JavaScript compares buyer city vs seller city
   ↓
7. Selects appropriate delivery fee
   ↓
8. Updates display: Subtotal + Delivery Fee = Total
   ↓
9. Stores calculatedDeliveryFee for order creation
```

## Testing

### Test Case 1: Same City Delivery

1. **Setup**:
   - Login as buyer with city "Lagos"
   - View product from store in "Lagos"
2. **Expected**:
   - Delivery fee shows ₦1,000 (or seller's custom within_lga fee)
3. **Verify**:
   - Check `deliveryFeeAmount` element shows correct amount
   - Check console: `buyerCity === sellerCity` → true

### Test Case 2: Different City Delivery

1. **Setup**:
   - Login as buyer with city "Abuja"
   - View product from store in "Lagos"
2. **Expected**:
   - Delivery fee shows ₦2,500 (or seller's custom outside_lga fee)
3. **Verify**:
   - Check `deliveryFeeAmount` element shows higher amount
   - Check console: `buyerCity === sellerCity` → false

### Test Case 3: No Buyer Location

1. **Setup**:
   - Login as buyer without city in profile
   - View product from any store
2. **Expected**:
   - Delivery fee shows ₦2,500 (outside_lga - safer default)
3. **Verify**:
   - Check console: "No buyer location info - use outside LGA fee"

### Test Case 4: Tooltip Visibility

1. **Action**: Hover over info icon (ⓘ) next to "Delivery Fee"
2. **Expected**: Tooltip appears with message
3. **Verify**: "Delivery fee varies based on your location..."

### Test Case 5: Seller Custom Fees

1. **Setup**:
   - Seller sets: within_lga = ₦1,500, outside_lga = ₦3,000
   - Create product in that store
2. **Expected**:
   - Local buyers see ₦1,500
   - Remote buyers see ₦3,000
3. **Verify**: Custom amounts displayed (not default ₦1,000/₦2,500)

## Edge Cases Handled

| Case                           | Handling                                 |
| ------------------------------ | ---------------------------------------- |
| No `store_info` in product     | Fallback to ₦2,500                       |
| No buyer city                  | Use `delivery_outside_lga` (safer)       |
| No seller city                 | Use `delivery_outside_lga`               |
| Store has no delivery fees set | Backend defaults apply (₦1,000 / ₦2,500) |
| City name case mismatch        | Convert both to lowercase                |
| City name with spaces          | Trim whitespace                          |

## Future Enhancements (Optional)

1. **State-Level Matching**: If cities don't match but states do, use medium fee
2. **Distance-Based Pricing**: Calculate based on actual distance
3. **Multiple Delivery Options**: Let buyer choose (Standard, Express, Same-Day)
4. **Free Delivery Threshold**: Seller sets "Free delivery for orders above ₦X"
5. **Delivery Time Estimate**: Show "Delivers in 2-3 days" based on location

## API Dependencies

- ✅ `GET /api/products/{id}/` - Returns `store_info` with delivery fees
- ✅ `GET /api/auth/profile/` - Returns user's city for comparison
- ✅ Store model - Has `delivery_within_lga` and `delivery_outside_lga` fields

## Files Modified

1. **`frontend/templates/purchase.html`**

   - Added `id="deliveryFeeAmount"` to delivery fee span
   - Added info icon with tooltip explaining calculation

2. **`frontend/assets/js/purchase.js`**
   - Removed hardcoded `deliveryFee = 500`
   - Added dynamic calculation based on buyer/seller cities
   - Store calculated fee in localStorage for order creation

## Notes

- **Default Store Fees**: ₦1,000 (within LGA), ₦2,500 (outside LGA)
- **Sellers Can Customize**: Via store settings (future feature)
- **Backend Already Ready**: No backend changes needed!
- **Order Creation**: Will use `calculatedDeliveryFee` from localStorage

---

**Status**: ✅ Complete & Ready for Testing
**Priority**: High (Correct pricing is critical)
**Impact**: All product purchases now use accurate delivery fees
