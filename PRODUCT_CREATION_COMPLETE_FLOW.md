# 📦 Complete Product Creation Flow - Step-by-Step Guide

## Overview
The product creation flow guides vendors through adding new items to the marketplace. The flow adapts based on product type (physical/digital) and product source (manufactured/handmade), with real-time validation and feedback.

---

## Entry Point: Access Product Creation

### How Vendors Start
1. **Login to account** (if not already logged in)
2. **Navigate to Vendor Dashboard**
   - URL: `/vendor/dashboard/`
3. **Click "Create New Product"** button
   - URL: `/vendor/products/create/`
4. **Land on empty product form**

### Form Structure
```
Product Form (vendor_product_form.html)
├── Physical Product Card (Default Selected)
├── Digital Product Card
└── Main Form (shown based on selection)
```

---

## Step 1: Choose Product Type (Physical vs Digital)

### User Interface
Two prominent cards at the top of the form:

```
┌─────────────────────┐    ┌─────────────────────┐
│   📦 PHYSICAL       │    │   💾 DIGITAL        │
│   PRODUCT           │    │   PRODUCT           │
│ (Default Selected)  │    │                     │
│ ✓                   │    │                     │
└─────────────────────┘    └─────────────────────┘
```

### What Happens When Selected

**Physical Product Selected:**
- ✅ Shows: Stock field
- ✅ Shows: Fulfillment method dropdown
- ✅ Shows: Delivery fee field
- ✅ Shows: Media section (images, videos, 3D models)
- ✅ Shows: Origin verification fields
- ❌ Hides: Digital file upload

**Digital Product Selected:**
- ✅ Shows: Digital file upload
- ✅ Shows: Stock limit field (for licenses)
- ❌ Hides: Physical product fields
- ✅ Shows: AI keywords field
- ✅ Categories filtered to "Digital Products" only

### JavaScript Logic
```javascript
// On page load or card click:
if (productType === 'physical') {
    show(['physical-section', 'stock-field', 'fulfillment', 'media'])
    hide(['digital-section'])
    filterCategoriesForPhysical()
} else if (productType === 'digital') {
    show(['digital-section', 'keywords'])
    hide(['physical-section', 'stock-field', 'fulfillment'])
    filterCategoriesForDigital()
}
```

---

## Step 2: Basic Product Information

### Fields Displayed (Always Visible)

#### A. Product Name
```
Field: product_type = CharField(max_length=255)
Validation:
- ✓ Required
- ✓ Max 255 characters
- ✓ Real-time character counter
- ✓ Appears in search results
Input: Text field with preview
Help Text: "The title customers will see when browsing"
```

#### B. Product Description
```
Field: description = TextField
Validation:
- ✓ Required
- ✓ Min 50 characters recommended
- ✓ Max 5000 characters
- ✓ Real-time word counter
Features:
- Text area with rich formatting
- "Enhance with AI" button (if existing product)
- Preview shows formatting
Help Text: "Describe features, benefits, conditions, etc."
```

#### C. Category Selection
```
Field: category = ForeignKey(Category)
Validation:
- ✓ Required
- ✓ Must be active category
- ✓ Physical vs Digital categories filtered
Method: Dropdown + Inline Picker
Features:
- Search across categories
- Breadcrumb for sub-categories
- Visual category cards (optional)
Help Text: "Select most appropriate category"
```

#### D. Brand (Optional)
```
Field: brand = CharField(max_length=255)
Validation:
- ✓ Optional
- ✓ Max 255 characters
- ✓ Appears in filters
Help Text: "Brand name (e.g., Apple, Nike)"
```

#### E. AI Keywords (Optional)
```
Field: keywords_for_ai = CharField(max_length=255)
Validation:
- ✓ Optional
- ✓ Comma-separated
- ✓ Max 255 characters
Help Text: "E.g., durable, eco-friendly, best-seller"
Purpose: Guides AI description enhancement
```

### User Experience
```
Form Section: Basic Information
┌─────────────────────────────────────────┐
│ Product Name *                          │
│ [____________________________________]  │
│  Help: The title customers will see     │
│                                         │
│ Product Description *                   │
│ [                                    ]  │
│ [   Type your description here...    ]  │
│ [   Minimum 50 characters            ]  │
│ [____________________________________]  │
│  Word count: 0/5000                     │
│  [Enhance with AI]                      │
│                                         │
│ Category *                              │
│ [______(Click to Select)___________▼]   │
│  Selected: (None)                       │
│                                         │
│ Brand (Optional)                        │
│ [____________________________________]  │
│                                         │
│ AI Keywords (Optional)                  │
│ [____________________________________]  │
│  E.g., durable, eco-friendly            │
└─────────────────────────────────────────┘
```

---

## Step 3: Pricing & Product Type

### Fields in This Section

#### A. Price (Physical Products)
```
Field: price = DecimalField(max_digits=10, decimal_places=2)
Validation:
- ✓ Required
- ✓ Min: $0.01
- ✓ Max: $9,999,999.99
- ✓ Decimal to 2 places
- ✓ Triggers artisan field visibility logic
Real-time Triggers:
- Price > $500? → Acquisition details becomes REQUIRED
- Price < $500? → Acquisition details stays OPTIONAL
Help Text: "Price in USD"
Input: Currency field with $ symbol
```

#### B. Product Condition
```
Field: product_condition = CharField(choices=...)
Choices:
- New (Default)
- Refurbished
- Used - Like New
- Used - Very Good
- Used - Good
- Used - Acceptable
- Collectible
Validation:
- ✓ Required
- ✓ Indicates product quality
Help Text: "Current condition of the item"
Input: Dropdown select
```

#### C. Stock Quantity (Physical Only)
```
Field: stock = PositiveIntegerField(default=0)
Validation:
- ✓ Required
- ✓ Min: 0
- ✓ Max: 2,147,483,647
- ✓ Must be integer
Help Text: "Number of items in stock. Set to 0 if out of stock"
Input: Number input with spinner
Visibility: Physical products only
```

### Example Display
```
Pricing & Type
┌─────────────────────────────────────────┐
│ Price (USD) *                           │
│ [____________$_____________]            │
│                                         │
│ Product Condition *                     │
│ [___________ New ___________▼]          │
│                                         │
│ Stock Quantity *                        │
│ [_____________ 0 _____________]         │
│  (Physical items in inventory)          │
└─────────────────────────────────────────┘
```

---

## Step 4: Product Type & Source (NEW - Artisan Verification)

### When This Section Appears
✅ **Always visible** - All product types can use artisan fields

### Fields in This Section

#### A. Product Type (Artisan)
```
Field: artisan_product_type = CharField(choices=...)
Choices:
- Manufactured/Branded (Default)
- Handmade/Artisan

Validation:
- ✓ Required
- ✓ Defaults to "Manufactured"

Help Text: "Is this a mass-produced/branded product or 
            handmade/artisan creation?"

Behavior:
- When "Manufactured":
  ❌ Hide acquisition fields
  ❌ Hide vendor badge preview
- When "Handmade":
  ✅ Show acquisition type dropdown
  ✅ Show info alert
  ✅ Trigger real-time verification

Input: Dropdown select
```

#### B. Acquisition Type (Shows for Handmade Only)
```
Field: acquisition_type = CharField(choices=...)
Choices (8 options - All equally valid):
1. I made/created this
   → Creator badge (+15% visibility boost)
2. Purchased new from manufacturer
   → Standard trust (no penalty)
3. Purchased used/secondhand
   → Reseller legitimate (no penalty)
4. On consignment from creator
   → Consignment badge (+10% visibility boost)
5. Estate sale/auction
   → Standard trust (no penalty)
6. Inherited/gifted
   → Standard trust (no penalty)
7. Sourced from verified supplier
   → Supplier badge (+5% visibility boost)
8. Other (explain)
   → Requires details in next field

Validation:
- ✓ Required when: product is "Handmade"
- ✓ Optional when: product is "Manufactured"

Help Text: "Tell customers where you got this product"

Input: Dropdown select
AJAX Triggers: Calls verify_artisan_product() on change
```

#### C. Acquisition Details (Conditional)
```
Field: acquisition_details = TextField(blank=True, null=True)
Max Length: Unlimited

Validation Rules:
1. When price ≤ $500:
   ❌ Field hidden
   
2. When price > $500 AND product = "Handmade":
   ✅ Field visible
   ✅ Field REQUIRED (marked with *)
   ✅ Must have content to save
   
3. When acquisition_type = "Other":
   ✅ Field always visible and required
   ✅ Prompts: "Please explain where you sourced this"

Help Text: "Provide details about how you acquired this 
           product. For high-value items (over $500), this 
           helps establish authenticity and boosts 
           customer confidence."

Real-Time Validation:
- Min length: 20 characters (for > $500 items)
- Max length: 2000 characters
- AJAX validates on blur event
- Error message if too short/empty

Input: Textarea field (3 rows)
Character Counter: Shows X/2000 characters
```

#### D. Vendor Badge Preview (Dynamic)
```
Visibility: Shows when applicable
- Product = "Handmade" AND
- Price ≥ $500 AND
- Valid acquisition_type selected AND
- Acquisition_details filled (if price > $500)

Display Format:
┌─────────────────────────────────────────┐
│ ✓ Badge Boost:                          │
│   Your Verified badge will boost        │
│   visibility by 15%                     │
└─────────────────────────────────────────┘

OR

┌─────────────────────────────────────────┐
│ ✓ Badge Boost:                          │
│   Your Creator badge will boost         │
│   visibility by 20%                     │
└─────────────────────────────────────────┘

Real-Time Update:
- Changes instantly when acquisition_type changes
- No page reload needed
- Shows immediately after AJAX verification
```

### Section Display
```
Product Type & Source
┌─────────────────────────────────────────┐
│ ℹ️ Artisan Product Verification:        │
│ Help customers understand where this    │
│ product comes from. This builds trust   │
│ and may boost visibility.               │
│                                         │
│ Product Type *                          │
│ [_____ Handmade/Artisan _____▼]         │
│ Select whether this is manufactured or  │
│ handmade.                               │
│                                         │
│ Acquisition Type *                      │
│ [___ I made/created this ___▼]          │
│ Tell customers where you got this       │
│ product.                                │
│                                         │
│ Acquisition Details *                   │
│ [                                    ]  │
│ [  Hand-painted ceramic pieces with ]   │
│ [  natural clay sourced from local   ]   │
│ [  suppliers...                       ]  │
│ [____________________________________]  │
│ (185/2000 characters)                   │
│                                         │
│ ✓ Badge Boost:                          │
│   Your Verified badge will boost        │
│   visibility by 15%                     │
└─────────────────────────────────────────┘
```

### JavaScript Logic
```javascript
document.addEventListener('DOMContentLoaded', function() {
    const artisanTypeSelect = document.querySelector('select[name="artisan_product_type"]');
    const priceInput = document.querySelector('input[name="price"]');
    const acquisitionTypeSelect = document.querySelector('select[name="acquisition_type"]');
    const acquisitionDetailsTextarea = document.querySelector('textarea[name="acquisition_details"]');
    
    function updateArtisanFields() {
        const isHandmade = artisanTypeSelect.value === 'handmade';
        const price = parseFloat(priceInput.value || 0);
        
        // Show/hide acquisition type based on product type
        acquisitionTypeWrapper.style.display = isHandmade ? 'block' : 'none';
        
        // Show/hide and require acquisition details based on price
        if (isHandmade && price > 500) {
            acquisitionDetailsWrapper.style.display = 'block';
            acquisitionDetailsTextarea.required = true;
            // Add asterisk to label
        } else {
            acquisitionDetailsWrapper.style.display = 'none';
            acquisitionDetailsTextarea.required = false;
        }
        
        // Trigger verification
        if (isHandmade) {
            verifyArtisanProduct();
        }
    }
    
    async function verifyArtisanProduct() {
        const response = await fetch('/api/verify-artisan-product/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                price: priceInput.value,
                acquisition_type: acquisitionTypeSelect.value,
                acquisition_details: acquisitionDetailsTextarea.value
            })
        });
        
        const result = await response.json();
        
        // Display badge boost if applicable
        if (result.vendor_badge && result.visibility_boost > 0) {
            vendorBadgePreview.style.display = 'block';
            badgeBoostText.textContent = 
                `Your ${result.vendor_badge} badge will boost visibility by ${result.visibility_boost}%`;
        }
    }
    
    // Event listeners
    artisanTypeSelect.addEventListener('change', updateArtisanFields);
    priceInput.addEventListener('change', updateArtisanFields);
    priceInput.addEventListener('blur', updateArtisanFields);
    acquisitionTypeSelect.addEventListener('change', verifyArtisanProduct);
    acquisitionDetailsTextarea.addEventListener('blur', verifyArtisanProduct);
    
    // Initialize
    updateArtisanFields();
});
```

---

## Step 5: Fulfillment & Delivery

### Fields in This Section (Physical Products Only)

#### A. Fulfillment Method
```
Field: fulfillment_method = CharField(choices=...)
Choices:
- Use Vendor's Default Setting (blank)
- Fulfilled by Gowbuy (FBA)
- Fulfilled by Vendor (FBM)

Validation:
- ✓ Optional
- ✓ Defaults to vendor profile setting
- ✓ Overrides vendor default if set

Help Text: "Select how this specific product will be 
           fulfilled. Leave blank to use your default."

Input: Dropdown select
```

#### B. Vendor's Delivery Fee (FBM Only)
```
Field: vendor_delivery_fee = DecimalField(decimal_places=2)

Visibility:
- Shows only if fulfillment_method = "Fulfilled by Vendor"
- Or if vendor profile default is FBM

Validation:
- ✓ Optional
- ✓ Min: $0.00
- ✓ Max: $9,999.99
- ✓ Decimal to 2 places

Help Text: "Set a delivery fee for this product if you 
           fulfill orders yourself. Leave blank to use 
           your profile default or free shipping."

Input: Currency field

Behavior:
- If left blank: Uses vendor profile default fee
- If filled: Overrides vendor profile default for this product
```

### Example Display
```
Fulfillment & Delivery
┌─────────────────────────────────────────┐
│ Product Fulfillment Method              │
│ [__ Use Vendor's Default Setting __▼]   │
│ Leave blank to use your default         │
│ setting.                                │
│                                         │
│ Vendor's Delivery Fee (if FBM)          │
│ [____________ $0.00 ____________]       │
│ Only applies if 'Fulfilled by Vendor'   │
└─────────────────────────────────────────┘
```

---

## Step 6: Media Uploads

### Fields in This Section

#### A. Product Images
```
Field: images = ManyToMany(ProductImage)

Validation:
- ✓ Optional but highly recommended
- ✓ Min: 1 image (recommended for conversion)
- ✓ Max: 20 images
- ✓ File types: JPG, PNG, WebP
- ✓ Max file size: 10MB per image
- ✓ Recommended dimensions: 1024x1024 or larger
- ✓ Auto-resizes on upload

Features:
- Drag & drop upload
- Multiple file selector
- Progress bar for each upload
- Image reordering (drag to reorder)
- Delete button for each image
- Preview thumbnails
- Image optimization (auto-compression)

Help Text: "Upload high-quality images. First image shown 
           as main product image. Recommended: 1024x1024px"
```

#### B. Product Videos (Optional)
```
Field: videos = ManyToMany(ProductVideo)

Validation:
- ✓ Optional
- ✓ Max: 5 videos
- ✓ File types: MP4, WebM
- ✓ Max file size: 500MB per video
- ✓ Max duration: 5 minutes

Features:
- Upload video or embed YouTube URL
- Auto-generates thumbnail from video
- Plays in product lightbox
- Mobile responsive playback

Help Text: "Upload product demo or review videos. 
           Improves conversion. Also accept YouTube URLs."
```

#### C. 3D Model (Optional)
```
Field: three_d_model = FileField(upload_to='products/3d_models/')

Validation:
- ✓ Optional
- ✓ File types: .glb, .gltf
- ✓ Max file size: 50MB
- ✓ No standard resolution limits

Features:
- Upload 3D model for interactive preview
- Viewer provided on product page
- Full 360° rotation
- Zoom controls
- Mobile support

Help Text: "Upload 3D model for interactive preview 
           (.glb or .gltf format)"

For Existing Products:
- "AI Generate 3D Model" button available
- Simulated 3D generation (currently)
```

### Example Display
```
Media Uploads
┌─────────────────────────────────────────┐
│ Product Images                          │
│ [Drag images here or click to select]   │
│ [Max 20 images, 10MB each]              │
│ ❌ File 1: image.jpg (2.5MB) ✓ Uploaded│
│ ❌ File 2: image2.png (3.1MB) ✓ Uploaded
│ ❌ File 3: video.mp4 (removed)          │
│                                         │
│ Reorder by dragging:                    │
│ [1️⃣  image.jpg]  [2️⃣  image2.png]      │
│                                         │
│ Videos (Optional)                       │
│ [Drag videos here or click to select]   │
│ [Max 5 videos, 500MB each, <5min]       │
│                                         │
│ 3D Model (Optional)                     │
│ [Choose File] [No file chosen]          │
│ [.glb or .gltf format, max 50MB]        │
│ [🤖 AI Generate 3D Model]               │
│  (Only for existing products)           │
└─────────────────────────────────────────┘
```

---

## Step 7: Product Verification (Origin Verification for Manufactured Items)

### When This Shows
✅ **Always visible** for manufactured/branded products

### Fields in This Section

#### A. Origin Country (Origin Verification)
```
Field: origin_country = CountryField

Validation:
- ✓ Required
- ✓ Must be valid country
- ✓ Used for automatic origin inference
- ✓ Triggers real-time verification

Help Text: "Country where product is manufactured"

Real-Time Validation:
- Calls AJAX endpoint on change
- Shows verification level (Low/Medium/High Risk)
- Highlights suspicious combinations
- Suggests alternative origins

Input: Country dropdown (searchable)
```

#### B. Device Identifier (For Electronics)
```
Field: device_identifier_type = CharField(choices=...)
Field: device_identifier_value = CharField

Valid Types:
- IMEI (Mobile phones, tablets with cellular)
- MAC Address (Wi-Fi devices, laptops)
- Serial Number (Laptops, consumer electronics)
- MEID (CDMA devices)
- ESN (Older CDMA devices)
- Device ID (Manufacturer specific)
- UPC/EAN Barcode (Universal Product Code)
- Batch/Lot Number (Production batch tracking)
- Model Number (Product model identifier)
- Not Applicable (Non-electronics)

Validation:
- ✓ Optional
- ✓ Type determines format requirements
- ✓ Value format validated based on type
- ✓ Can be used to verify authenticity

Help Text: "For electronics: Device identifier helps 
           verify authenticity. Optional but recommended."

Real-Time Validation:
- Shows if ID is valid format
- Checks against known fakes
- Suggests improvements
```

#### C. Authenticity Status
```
Field: authenticity_status = CharField(choices=...)
Choices:
- Authentic (Original) - Default
- Refurbished
- Replica/Homage
- Unknown

Validation:
- ✓ Required
- ✓ Affects listing visibility
- ✓ Defaults to "Authentic"

Help Text: "Declare the authenticity status of product"

Impact:
- Authentic: Normal visibility
- Refurbished: Flagged but allowed
- Replica: Requires extra verification
- Unknown: May reduce visibility
```

#### D. Brand & Manufacturer Info
```
Fields:
- brand = CharField (max 255)
- manufacturer = CharField (max 255)
- manufacturer_address = CharField (max 255)
- model_number = CharField (max 100)
- batch_lot_number = CharField (max 100)

All Optional but recommended for:
- Electronics
- Branded items
- High-value products

Validation:
- ✓ Max length limits enforced
- ✓ Real-time brand lookup
- ✓ Suggests corrections
- ✓ Checks against brand database

Real-Time Checks:
- Brand verification against 50+ known brands
- Country-brand compatibility check
- Price reasonableness check
```

#### E. Certification Numbers
```
Field: certification_numbers = CharField (comma-separated)

Examples:
- FCC (USA electronics)
- CE (EU compliance)
- RoHS (Hazardous substances)
- UL (Safety certification)
- etc.

Validation:
- ✓ Optional but recommended
- ✓ Comma-separated list
- ✓ Can be multiple certifications
- ✓ Format validation for known certs

Help Text: "Regulatory certifications if applicable
           (e.g., FCC, CE, RoHS). Comma-separated."

Real-Time Checks:
- Validates certification format
- Checks against known certifications
- Suggests relevant certs for product type
```

### Verification Level Display
```
The form shows a colored alert:

LOW RISK (Green):
✓ Verification Level: LOW RISK
  All provided information checks out.
  Your product may qualify for additional
  visibility boost.

MEDIUM RISK (Yellow):
⚠️ Verification Level: MEDIUM RISK
   Some information requires verification.
   Product will appear but with review flag.
   Please add: [list missing items]

HIGH RISK (Red):
❌ Verification Level: HIGH RISK
   Product combination seems suspicious.
   Manual admin review required before listing.
   Reasons: [list issues]
```

---

## Step 8: Digital Product Specific Fields

### When This Shows
✅ **Only when product_type = "Digital"**

### Fields in This Section

#### A. Digital File Upload
```
Field: digital_file = FileField(upload_to='products/digital/')

Validation:
- ✓ Required for digital products
- ✓ Max file size: 500MB
- ✓ File types allowed: Any (PDF, ZIP, EXE, etc.)

Features:
- Secure file upload
- Automatic virus scan (if available)
- Direct download link (after purchase)
- Multiple download attempts allowed
- License key generation (if applicable)

Help Text: "Upload your digital product file 
           (PDF, ZIP, software, etc.)"

Display:
- Shows uploaded filename
- File size display
- Delete & reupload options
```

#### B. Stock/License Limit
```
Field: stock = PositiveIntegerField

For Digital Products:
- Represents license limit (not actual stock)
- Leave blank = unlimited downloads/licenses
- Set to number = limit sales to that number

Validation:
- ✓ Optional (blank = unlimited)
- ✓ Must be positive integer if set
- ✓ No upper limit technically

Help Text: "Leave blank for unlimited downloads.
           Enter a number to limit how many copies 
           can be sold (e.g., for limited licenses)."

Use Cases:
- Unlimited: Courses, ebooks, plugins
- Limited: 100 licenses for software
- Single: Exclusive custom work
```

### Example Display
```
Digital Product Details
┌─────────────────────────────────────────┐
│ Digital File *                          │
│ [Choose File] [No file chosen]          │
│ Upload your digital product file        │
│ (PDF, ZIP, etc.)                        │
│ (Max 500MB)                             │
│                                         │
│ Stock/License Limit (Optional)          │
│ [___________ (blank) ___________]       │
│ Leave blank for unlimited licenses.     │
│ Enter a number to limit copies sold.    │
└─────────────────────────────────────────┘
```

---

## Step 9: Submit Product

### Buttons at Form Bottom

#### A. Cancel Button
```
Action: Go back to product list
URL: /vendor/products/
Effect: Discards all form changes (if unsaved)
```

#### B. Create Product Button (Create Form)
```
Text: "Create Product"
Action: Validates all required fields
        Submits form via POST
        Processes all data
        Stores in database
Response:
- Success: Redirects to product detail page
           Shows success message
- Error: Shows validation errors in red
         Highlights problematic fields
         Preserves form data
```

#### C. Save Changes Button (Update Form)
```
Text: "Save Changes"
Action: Updates existing product
        Validates changes only
        Preserves existing media if not changed
Response:
- Success: Redirects to product page
           Shows "Updated successfully"
- Error: Shows validation errors
         Allows retry
```

### Validation Summary (Before Submit)
```
VALIDATION CHECKLIST:
✓ Product Name - min 3 chars, max 255
✓ Description - min 50 chars, max 5000
✓ Category - must be selected
✓ Price - must be > $0
✓ Product Condition - must be selected
✓ Stock - required for physical, must be >= 0
✓ Origin Country - required for physical
✓ Product Images - at least 1 recommended
✓ Digital File - required if product_type = digital
✓ Acquisition Details - required if handmade AND price > $500

All checks pass? → Save button enabled ✅
Some checks fail? → Save button disabled + shows errors ❌
```

---

## Complete Flow Diagram

```
START
  │
  ├─ Log in to vendor account
  │
  ├─ Navigate to Create Product
  │
  ├─ STEP 1: Choose Product Type
  │  ├─ Physical or Digital?
  │  └─ Form adapts to selection
  │
  ├─ STEP 2: Basic Info
  │  ├─ Name
  │  ├─ Description
  │  ├─ Category
  │  ├─ Brand (optional)
  │  └─ AI Keywords (optional)
  │
  ├─ STEP 3: Pricing & Type
  │  ├─ Price
  │  ├─ Condition
  │  └─ Stock (physical only)
  │
  ├─ STEP 4: Product Type & Source (NEW)
  │  ├─ Artisan Product Type
  │  │  ├─ Manufactured (hide fields)
  │  │  └─ Handmade (show fields)
  │  ├─ Acquisition Type (if handmade)
  │  ├─ Acquisition Details (if handmade & price > $500)
  │  └─ Vendor Badge Preview (real-time)
  │
  ├─ STEP 5: Fulfillment (physical only)
  │  ├─ Fulfillment Method
  │  └─ Delivery Fee (if FBM)
  │
  ├─ STEP 6: Media
  │  ├─ Images
  │  ├─ Videos (optional)
  │  └─ 3D Model (optional)
  │
  ├─ STEP 7: Verification
  │  ├─ Origin Country (physical only)
  │  ├─ Device Identifier (electronics)
  │  ├─ Authenticity Status
  │  ├─ Brand & Manufacturer
  │  └─ Certifications (optional)
  │
  ├─ STEP 8: Digital-Specific (if digital)
  │  ├─ Digital File Upload
  │  └─ License Limit (optional)
  │
  ├─ STEP 9: Validation
  │  ├─ All required fields filled?
  │  ├─ All values in valid format?
  │  └─ Handmade > $500 has details?
  │
  ├─ STEP 10: Submit
  │  ├─ Click "Create Product"
  │  ├─ Form sent to server
  │  ├─ Server validates again
  │  ├─ Data stored in database
  │  └─ Product created
  │
  └─ SUCCESS
     ├─ Redirects to product page
     ├─ Shows success message
     └─ Product visible to customers (pending admin approval if needed)
```

---

## Database Storage

### Data Stored in Database

```python
Product(
    # Basic Info
    name="Hand-painted Ceramic Vase",
    description="Beautiful handmade ceramic vase...",
    category_id=15,  # Artisan Products
    brand="None",
    
    # Pricing
    price=Decimal("599.99"),
    product_condition="new",
    stock=3,
    
    # ARTISAN VERIFICATION (NEW)
    artisan_product_type="handmade",
    acquisition_type="i_created",
    acquisition_details="Hand-painted with traditional techniques using...",
    
    # Fulfillment
    product_type="physical",
    fulfillment_method="vendor",
    vendor_delivery_fee=Decimal("15.00"),
    
    # Media
    images=[...],  # List of ProductImage objects
    videos=[...],  # List of ProductVideo objects
    three_d_model=None,
    
    # Verification (Origin)
    origin_country="US",
    authenticity_status="authentic",
    device_identifier_type="none",
    device_identifier_value=None,
    brand=None,
    manufacturer=None,
    
    # Metadata
    is_active=True,
    is_featured=False,
    created_at=datetime.now(),
    updated_at=datetime.now(),
    
    # Relationships
    vendor_id=42,
)
```

---

## Real-Time Validations Happening

### Client-Side (JavaScript)
1. **Product Type Change** → Show/hide form sections
2. **Price Change** → Show/hide acquisition details requirement
3. **Artisan Type Change** → Show/hide acquisition fields
4. **Acquisition Type Change** → Call AJAX verification, show badge
5. **Acquisition Details Change** → Call AJAX validation, check length

### Server-Side (AJAX Endpoints)
1. **`/api/verify-artisan-product/`** → Calculate tier, visibility boost, badge
2. **`/api/validate-acquisition-info/`** → Check details for high-value items
3. **`/api/validate-product-origin/`** → Check brand/country/price combinations
4. **`/api/enhance-product-description/`** → AI enhancement suggestion

### Form Submission (Django Backend)
1. CSRF token verification
2. Required field validation
3. Field type validation (decimal, integer, text length)
4. Foreign key existence verification
5. File upload validation (images, videos, 3D model)
6. Duplicate product check
7. Vendor ownership verification
8. Model save (creates/updates database record)

---

## Error Handling

### Common Validation Errors

```
❌ "Product name is required"
   → Fill in the Product Name field

❌ "Description must be at least 50 characters"
   → Write more details about your product

❌ "Please select a category"
   → Click Category field and choose one

❌ "Price must be greater than 0"
   → Enter a valid price (e.g., 49.99)

❌ "Acquisition details is required for items over $500"
   → Fill in the Acquisition Details field when price > $500

❌ "At least one product image is required"
   → Upload at least 1 image

❌ "Digital file is required for digital products"
   → Upload your digital product file

❌ "Invalid file format for images (only JPG, PNG, WebP)"
   → Use JPG, PNG, or WebP format

❌ "File size exceeds maximum (10MB for images)"
   → Compress images to under 10MB

❌ "Invalid country selected"
   → Choose a valid country from dropdown
```

---

## Example: Complete Product Creation Scenario

### Scenario: Vendor Creates Handmade Ceramic Product

**Starting Position:**
- Vendor logged in
- On vendor dashboard
- Clicks "Create New Product"

**Form Completion:**

```
STEP 1: Product Type
Select: Physical Product ✓

STEP 2: Basic Info
Product Name: "Hand-Painted Ceramic Coffee Set"
Description: "Beautifully crafted 6-piece ceramic coffee 
             set with hand-painted patterns. Each piece 
             glazed with food-safe finishes. Perfect gift 
             for coffee lovers."
Category: "Artisan Products > Ceramics"
Brand: (left blank)
AI Keywords: "handmade, coffee, ceramic, gift, artisan"

STEP 3: Pricing & Type
Price: $599.99
Condition: New
Stock: 5

STEP 4: Product Type & Source
Product Type: Handmade/Artisan ← Shows acquisition fields!
Acquisition Type: "I made/created this" ← Creator badge!
Acquisition Details: "Each piece hand-thrown on pottery 
                    wheel and hand-painted with cobalt 
                    blue designs inspired by traditional 
                    Asian pottery. Finished with food-safe 
                    ceramic glaze."
                    ← Required because price > $500!
Vendor Badge Preview: ✓ "Your Creator badge will boost 
                    visibility by 20%"

STEP 5: Fulfillment & Delivery
Fulfillment Method: "Fulfilled by Vendor"
Delivery Fee: $12.50

STEP 6: Media
Images: [upload 5 images]
Videos: (leave blank)
3D Model: (leave blank)

STEP 7: Verification
Origin Country: "United States"
Device Identifier: N/A
Authenticity: "Authentic (Original)"
Brand: (leave blank)

STEP 8: Submit
Click "Create Product" button
↓
Form validates ✓ All checks pass
↓
Form submitted to server
↓
Server validates ✓ All checks pass
↓
Data saved to database
↓
Product created successfully ✓
↓
Redirect to product page
Display: "Product created successfully! Your product is now visible to customers."
```

**Result:**
- Product stored in database with all artisan fields
- Creator badge automatically applied
- +20% visibility boost applied
- Product visible on marketplace
- Customers see "Created by Vendor Name" badge

---

## Summary: Key Flow Points

1. ✅ **Product Type Selection** - Determines which fields show
2. ✅ **Basic Information** - Always required for all products
3. ✅ **Pricing & Artisan Type** - NEW: Includes artisan verification
4. ✅ **Acquisition Transparency** - NEW: Where did vendor get it?
5. ✅ **Real-Time Validation** - Fields adapt as user fills form
6. ✅ **Vendor Badges** - NEW: Show visibility boost potential
7. ✅ **Media Upload** - Images, videos, 3D models
8. ✅ **Origin Verification** - For manufactured products
9. ✅ **Form Submission** - Multi-level validation then save
10. ✅ **Success** - Product created and visible

---

**Last Updated**: February 4, 2026
**System Status**: ✅ PRODUCTION READY
