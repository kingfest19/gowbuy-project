# Artisan & Handmade Product Verification System

**Philosophy:** "Trust but Verify" - Lower vendor friction, reputation-based filtering

---

## 🎯 Overview

This system handles verification for three types of products:

1. **Manufactured/Branded** (Already supported ✓)
   - Electronics, branded items, official products
   - Uses origin verification engine
   - Brand, certifications, price checks

2. **Handmade/Artisan** (NEW - This System)
   - Paintings, handcrafted items, custom products
   - Vendor can be creator OR reseller
   - Trust-based, no proof-of-creation required

3. **High-Value Items** (>$500 - NEW - This System)
   - Luxury art, investment collectibles
   - Simple transparency: "Where did you get this?"
   - Light-touch verification

---

## 🚀 Key Features

### No Proof-of-Creation Required
```
❌ OLD: "You must prove you made this"
✅ NEW: "Tell us where you got it"
```

### Vendor-Agnostic
```
Vendor can be:
✓ The artist/creator
✓ A legitimate reseller
✓ An estate sale buyer
✓ A consignment dealer

All are equally valid!
```

### Reputation-Based Trust
```
New Vendor (0 sales)
  └─ Easy entry, basic requirements
     └─ Escrow protection for first 3 sales
        └─ Good reviews lead to higher tier
           └─ Trusted Vendor badge
              └─ Master Craftsman status
```

### Progressive Requirements
```
Basic (<$500):
├─ Photos (3+)
├─ Title
├─ Description
└─ Category

High-Value ($500-$2000):
├─ Everything above
└─ + "How did you acquire this?" (dropdown)

Luxury (>$2000):
├─ Everything above
└─ + Certificate (if available)
└─ + Provenance details (recommended)
```

---

## 📊 Vendor Tiers

### Tier 1: New Seller
```
Sales: 0
Rating: Any
Trust Score: 50
Badge: None
Status: Listed with escrow protection
Action: Build reputation through sales
```

### Tier 2: Verified Seller
```
Sales: 3+
Rating: 4.0★+
Trust Score: 70
Badge: ✓ Verified Seller
Status: Auto-approved listings
Action: Featured in category
```

### Tier 3: Trusted Artisan
```
Sales: 10+
Rating: 4.5★+
Trust Score: 85
Badge: ✓✓ Trusted Artisan
Status: Premium positioning
Action: Higher visibility in search
```

### Tier 4: Master Craftsman
```
Sales: 50+
Rating: 4.8★+
Trust Score: 95
Badge: ✓✓✓ Master Craftsman
Status: Premium features unlocked
Action: Homepage featured, lower fees
```

---

## 📋 Acquisition Types (For High-Value Items)

When vendor lists item >$500, they select:

```
1. "I made/created this item"
   └─ Artist/creator
   └─ Visibility boost: +15%
   
2. "Purchased new from manufacturer/brand"
   └─ Legitimate reseller
   └─ For branded handmade items
   
3. "Purchased used/secondhand"
   └─ Reseller of used goods
   └─ Most common for collectibles
   
4. "On consignment from creator"
   └─ Selling on behalf of artist
   └─ Both parties identified
   
5. "Estate sale/auction"
   └─ Legitimate previous acquisition
   └─ Often valuable/collectible
   
6. "Inherited/gifted"
   └─ Family heirlooms
   └─ Personal collection sale
   
7. "Sourced from verified supplier"
   └─ Wholesale/distributor source
   └─ Good for resellers
   
8. "Other (please explain)"
   └─ Free-text explanation
   └─ Examples: "Found at flea market"
```

All are equally acceptable! We just want transparency.

---

## 🔍 Verification Logic

### Step 1: Determine Vendor Tier
```python
sales = vendor.sales_count
rating = vendor.average_rating

if sales >= 50 and rating >= 4.8:
    tier = "master"  # Trust score: 95
elif sales >= 10 and rating >= 4.5:
    tier = "trusted"  # Trust score: 85
elif sales >= 3 and rating >= 4.0:
    tier = "verified"  # Trust score: 70
else:
    tier = "new"  # Trust score: 50
```

### Step 2: Check Documentation Quality
```python
points = 0

# Photos (good, adequate, or poor)
if images >= 5:
    points += 15
elif images >= 3:
    points += 10
else:
    points -= 5

# Description quality
if description_length >= 300:
    points += 7
elif description_length >= 150:
    points += 4

# Add more points for extras...
```

### Step 3: Check Price Thresholds
```python
if price >= $2000:
    # Luxury item checks
    - Acquisition info required
    - Certificate bonus if available
    - Provenance details helpful
    
elif price >= $500:
    # High-value checks
    - Acquisition info required
    - All acquisition types OK
    
else:
    # Basic items
    - No acquisition info needed
    - Just good photos & description
```

### Step 4: Calculate Final Score
```python
score = vendor_trust_score  # 50-95 base
score += documentation_bonus  # 0-25
score += price_threshold_bonus  # 0-20

max_score = 100

Result:
- 75+: APPROVED (immediate listing)
- 60-75: APPROVED_WITH_REVIEW (24-48hr manual check)
- <60: NEEDS_REVIEW (requires vendor follow-up)
```

---

## 💡 Real-World Examples

### Example 1: New Artist Selling Painting
```
Vendor: Sarah (First sale)
Product: Oil painting ($350)
Sales: 0 | Rating: N/A

Tier: New Seller (Trust: 50)
Photo Quality: 5 photos (+15)
Description: 250 characters (+7)
Price: <$500, no acquisition needed
Total: 50 + 15 + 7 = 72

Result: ✓ APPROVED WITH REVIEW (24 hrs)
```

### Example 2: Trusted Reseller Selling Used Collectible
```
Vendor: John (Established reseller)
Product: Vintage watch ($1,500)
Sales: 25 | Rating: 4.6★

Tier: Trusted Artisan (Trust: 85)
Photo Quality: 8 photos (+15)
Description: 400 characters (+7)
Acquisition: "Estate sale" (+15)
Certificate: Yes (+10)
Total: 85 + 15 + 7 + 15 + 10 = 132 → 100 (capped)

Result: ✓ APPROVED IMMEDIATELY
```

### Example 3: New Vendor Selling Luxury Item
```
Vendor: Mike (First sale)
Product: Modern art piece ($3,000)
Sales: 0 | Rating: N/A

Tier: New Seller (Trust: 50)
Photo Quality: 3 photos (+10)
Description: 150 characters (+4)
Acquisition: "I created it" (+10)
Price >$2000: Needs provenance
Total: 50 + 10 + 4 + 10 = 74

Result: ⚠️ NEEDS_REVIEW 
Next Step: Admin contacts vendor for artist statement
```

---

## 🎁 Benefits of This Approach

### For Vendors
```
✓ Easy entry - list in 5 minutes
✓ No scary documentation
✓ Resellers welcome
✓ Clear path to trust badges
✓ Build reputation naturally
✓ No discrimination between creators/resellers
```

### For Creators
```
✓ Can identify as artist (badge)
✓ Optional: Share creation story
✓ Visibility boost for creators
✓ Community recognition
✓ Same easy listing as resellers
```

### For Resellers
```
✓ No second-class treatment
✓ Simple transparency on acquisition
✓ Build reputation through sales
✓ Access all vendor tiers
✓ Same badge/benefit system
```

### For Customers
```
✓ Know where items came from
✓ Can support creators directly
✓ Can buy from trusted resellers
✓ Protected on expensive items
✓ Escrow for new vendors
```

### For Platform
```
✓ Larger vendor base (easy entry)
✓ Higher vendor satisfaction
✓ Lower churn/abandonment
✓ More handmade listings
✓ Community-driven quality
✓ Reputation system self-regulates
```

---

## 📱 AJAX Endpoints

### 1. Verify Artisan Product
```
POST /api/verify-artisan-product/

Request:
{
    'price': 350,
    'vendor_sales': 5,
    'vendor_rating': 4.2,
    'product_title': 'Handmade Painting',
    'description': 'Beautiful landscape...',
    'category': 'Art',
    'acquisition_type': 'created',
    'acquisition_details': 'Painted in my studio',
    'image_count': 5
}

Response:
{
    'success': true,
    'valid': true,
    'score': 85,
    'confidence': 'High',
    'status': 'APPROVED',
    'vendor_tier': 'verified',
    'reasoning': 'Good vendor reputation | 5 clear photos | Item source verified',
    'requirements_met': ['✓ Photos', '✓ Description', '✓ Acquisition'],
    'next_steps': ['Your product is approved!', 'Tip: More photos = more visibility'],
    'vendor_badge': {'text': 'Verified Seller', 'color': 'blue'},
    'visibility_boost': 1.15
}
```

### 2. Validate Acquisition Info
```
POST /api/validate-acquisition-info/

Request:
{
    'price': 1500,
    'acquisition_type': 'purchased_used',
    'acquisition_details': 'Estate sale 2024'
}

Response:
{
    'success': true,
    'valid': true,
    'message': null,
    'required': true
}
```

### 3. Get Acquisition Options
```
GET /api/get-acquisition-options/

Response:
{
    'success': true,
    'options': [
        ['created', 'I made/created this item'],
        ['purchased_new', 'Purchased new...'],
        ['purchased_used', 'Purchased used...'],
        ...
    ]
}
```

### 4. Get Vendor Tier Requirements
```
POST /api/get-vendor-tier-requirements/

Request:
{
    'vendor_sales': 15,
    'vendor_rating': 4.6,
    'price': 800
}

Response:
{
    'success': true,
    'vendor_tier': 'trusted',
    'tier_info': {
        'label': 'Trusted Artisan',
        'description': '10+ sales with 4.5★ average',
        'trust_score': 85
    },
    'requirements': {
        'basic': ['Title', 'Description', 'Price', 'Photos', 'Category'],
        'high_value': [
            'How did you acquire this item?',
            'Examples: Made it, Purchased...'
        ]
    }
}
```

---

## 🛠️ Implementation Checklist

### Backend
- [x] ArtisanVerificationEngine class
- [x] Tier-based reputation system
- [x] Progressive requirements
- [x] AJAX endpoints (4 total)
- [x] URL routing
- [x] View imports

### Frontend
- [ ] Product type selector (manufactured vs handmade)
- [ ] Conditional field display based on price
- [ ] Acquisition info dropdown (for >$500)
- [ ] Real-time verification display
- [ ] Vendor tier badge display
- [ ] Visibility boost indicator

### Database
- [ ] Add product_type field to Product model
- [ ] Add acquisition_type field
- [ ] Add acquisition_details field
- [ ] Add vendor_verified_date field (optional)
- [ ] Migration script

### Admin
- [ ] Dashboard showing new listings
- [ ] Filter by product type
- [ ] Quick review interface for >$2000 items
- [ ] Bulk approve/flag system
- [ ] Vendor tier management

---

## 📊 Scoring Examples

### Basic Item (<$500)
```
Vendor Trust: 50 points (new)
Photos (5): +15 points
Description (300 chars): +7 points
Category: +2 points
Images: +3 points
TOTAL: 77 → APPROVED ✓
```

### Handmade Item ($350)
```
Vendor Trust: 70 points (verified)
Photos (3): +10 points
Description (150 chars): +4 points
Artist Statement: +5 points
TOTAL: 89 → APPROVED ✓
```

### Resold Collectible ($1,200)
```
Vendor Trust: 85 points (trusted)
Photos (6): +15 points
Description (400 chars): +7 points
Acquisition: "Estate sale" +15 points
Certificate: Yes +10 points
TOTAL: 132 → 100 (capped) → APPROVED ✓✓✓
```

### Luxury Item First Sale ($3,500)
```
Vendor Trust: 50 points (new)
Photos (4): +12 points
Description (200 chars): +5 points
Acquisition: "I created it" +10 points
Provenance: No documentation
TOTAL: 77 → APPROVED WITH REVIEW ⚠️
(Admin reviews, can request artist statement)
```

---

## 🎓 Key Principles

1. **Trust First** - Start with positive assumption, not suspicion
2. **Transparency** - Ask where item came from, don't demand proof
3. **Reputation Matters** - Good track record earns badges
4. **Vendor Agnostic** - Treat creators and resellers equally
5. **Progressive** - More requirements for expensive items only
6. **Fair** - No discrimination based on vendor background
7. **Community** - Let reviews and ratings self-regulate quality

---

## ⚡ Quick Reference

**<$500:** Photos, Title, Description, Category
**$500-$2000:** + Acquisition type (dropdown)
**>$2000:** + Certificate (if available), + Provenance details

**Vendor Tiers:**
- New: 0 sales, 50 trust score
- Verified: 3+ sales, 4.0★, 70 trust score, get badge
- Trusted: 10+ sales, 4.5★, 85 trust score, featured
- Master: 50+ sales, 4.8★, 95 trust score, premium

**All acquisition sources accepted equally:**
- Made it myself ✓
- Bought from store ✓
- Estate sale ✓
- Inherited ✓
- Reselling ✓

---

**Status:** Ready to implement
**Vendor Impact:** Positive (easy entry)
**Quality Impact:** Good (reputation-based)
**Growth Impact:** Fast (lower barriers)

