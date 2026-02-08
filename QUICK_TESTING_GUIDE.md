# 🧪 Quick Testing Guide - Artisan Product Verification

## Test Scenario 1: Create a Handmade Product (< $500)

**Expected Behavior:**
- Acquisition type dropdown appears
- Acquisition details field is optional
- No vendor badge shown

**Steps:**
1. Go to Vendor Dashboard → Create Product
2. Enter basic info (Name, Description, Category)
3. Set **Price: $150**
4. Select **Product Type: Handmade**
5. Choose **Acquisition Type: "I made/created this"**
6. Leave Acquisition Details empty
7. Click Save
8. ✅ Product created (no errors)

---

## Test Scenario 2: Create a Handmade Product (> $500, with Details)

**Expected Behavior:**
- Acquisition type dropdown appears
- Acquisition details field becomes **REQUIRED** (marked with *)
- Vendor badge preview shows visibility boost
- System accepts & saves all data

**Steps:**
1. Go to Vendor Dashboard → Create Product
2. Enter basic info
3. Set **Price: $2500** (luxury item)
4. Select **Product Type: Handmade**
5. Choose **Acquisition Type: "I made/created this"**
6. Enter **Acquisition Details**: "Hand-carved wooden sculptures, 3D design process with CNC finishing"
7. Click Save
8. ✅ Product created successfully
9. ✅ Visibility boost badge should display

---

## Test Scenario 3: Switch from Manufactured to Handmade

**Expected Behavior:**
- When you switch to Handmade, new fields appear
- When you switch back to Manufactured, fields hide
- Form remembers your selections when toggling

**Steps:**
1. Open existing manufactured product
2. Scroll to "Product Type & Source" section
3. Select **Handmade**
4. ✅ Acquisition fields appear immediately
5. Select **Handmade** → **Manufactured**
6. ✅ Acquisition fields disappear
7. Select **Handmade** again
8. ✅ Your previous acquisition choice is remembered

---

## Test Scenario 4: Price Validation (< $500 vs > $500)

**Expected Behavior:**
- Prices < $500: acquisition details optional
- Prices > $500: acquisition details required

**Steps:**
1. Create handmade product
2. Set **Price: $450**
3. ✅ Acquisition Details shows as optional (no asterisk)
4. Change **Price: $550**
5. ✅ Acquisition Details now shows as required (asterisk appears)
6. Leave details empty and try to save
7. ✅ Form should show validation error OR warning
8. Add details: "Purchased used from estate sale"
9. ✅ Save successful

---

## Test Scenario 5: All 8 Acquisition Types

Test each acquisition type works properly:

**Steps:**
1. Create handmade product ($600+)
2. Try each acquisition type:
   - ✅ "I made/created this"
   - ✅ "Purchased new from manufacturer"
   - ✅ "Purchased used/secondhand"
   - ✅ "On consignment from creator"
   - ✅ "Estate sale/auction"
   - ✅ "Inherited/gifted"
   - ✅ "Sourced from verified supplier"
   - ✅ "Other (explain)" → Add note in details field

3. Save each one successfully
4. ✅ All options work without errors

---

## Test Scenario 6: AJAX Verification Feedback

**Expected Behavior:**
- Badge preview shows when appropriate
- Visibility boost percentage displayed
- Response under 1 second

**Steps:**
1. Create handmade product with price > $500
2. Fill in acquisition type and details
3. Watch for vendor badge preview to appear
4. ✅ Should show something like: "Your Verified badge will boost visibility by 15%"
5. Change acquisition type
6. ✅ Badge preview updates in real-time (no page reload)

---

## Test Scenario 7: Database Verification

**Check that data is saved correctly:**

```bash
# SSH into server or use Django shell
python manage.py shell

# Check that a product was created with new fields
from core.models import Product
p = Product.objects.latest('created_at')
print(p.artisan_product_type)  # Should print 'handmade'
print(p.acquisition_type)       # Should print selected type
print(p.acquisition_details)    # Should print your description
```

---

## Common Issues & Troubleshooting

### Issue: Acquisition fields not appearing
- Check browser console for JavaScript errors (F12 → Console tab)
- Ensure product type value is 'handmade' (not 'handcraft')
- Clear browser cache and refresh

### Issue: "Acquisition Details" marked required but shouldn't be
- Check if price is actually > $500
- Try clearing form and re-entering price
- Check browser console for JS errors

### Issue: Form won't save when > $500
- Make sure acquisition details field is filled
- Check for red validation messages below fields
- Ensure no other required fields are empty

### Issue: Badge preview not showing
- Make sure product is marked as "Handmade"
- Make sure price > $500
- Try filling in acquisition type first
- Check browser console for AJAX errors

---

## Success Criteria

All of these should work:

- [ ] Create manufactured product (no artisan fields shown)
- [ ] Create handmade product < $500 (acquisition type optional)
- [ ] Create handmade product > $500 (acquisition details required)
- [ ] Switch between manufactured/handmade (fields appear/disappear)
- [ ] Try all 8 acquisition types (all save successfully)
- [ ] See vendor badge preview (for high-value handmade items)
- [ ] Check database (data stored in correct fields)
- [ ] No JavaScript errors in browser console
- [ ] Form validation works as expected
- [ ] AJAX endpoints respond quickly (< 1 second)

---

## Test Data Suggestions

| Product | Type | Price | Acquisition | Expected Result |
|---------|------|-------|-------------|-----------------|
| Ceramic Vase | Handmade | $150 | "I made/created this" | ✅ Save without details |
| Leather Bag | Handmade | $750 | "I made/created this" | ✅ Requires details, shows badge |
| Vintage Camera | Handmade | $400 | "Estate sale/auction" | ✅ Save without details |
| Diamond Ring | Handmade | $3000 | "Inherited/gifted" | ✅ Requires details, shows badge |
| iPhone 15 | Manufactured | $999 | N/A (no fields) | ✅ Save without artisan info |
| Artwork Print | Handmade | $200 | "Consignment" | ✅ Save, consider showing badge |

---

**Testing Time Estimate**: 30-45 minutes
**Recommended**: Test at least scenarios 1-5 before going live
