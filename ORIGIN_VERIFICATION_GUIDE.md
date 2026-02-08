# Product Origin Verification System

## Overview

The Origin Verification System automatically validates whether a vendor's claimed product origin is legitimate by cross-referencing product details against known patterns, certifications, manufacturer information, and device identifiers.

## Architecture

### Core Components

1. **OriginVerificationEngine** (`origin_verification.py`)
   - Main verification logic
   - Rule-based matching against product details
   - Confidence scoring (0-100)
   - Mismatch detection

2. **AJAX Endpoints** (`origin_verification_views.py`)
   - Real-time validation during product creation
   - Authenticity risk assessment
   - Origin suggestions from similar products

3. **Management Command** (`verify_product_origins.py`)
   - Batch verification of existing products
   - Admin reporting of suspicious claims
   - Result persistence

## Verification Rules

The system checks product details against 5 main categories:

### 1. **Brand Verification** 
- Maps 50+ brands to their known origins
- Detects when a brand claims origin from a different country
- Examples:
  - Apple claiming India origin → ⚠️ Flag
  - Samsung claiming Korea origin → ✓ Valid
  - Nike claiming Vietnam origin → ⚠️ Unusual but possible

### 2. **Manufacturer Location Check**
- Analyzes manufacturer name and address for geographic clues
- Looks for city/country mentions (e.g., "Shenzhen" → China)
- Flags mismatches between address and claimed origin

### 3. **Device Identifier Verification** (Electronics only)
- IMEI prefix analysis (device type indicators)
- MAC address patterns
- Serial number format verification
- Can identify device manufacturing region

### 4. **Certification Analysis**
- Checks FCC (USA), CE Mark (EU), CCC (China), PSE (Japan), etc.
- Knows which certifications are issued by which countries
- Flags certificate/origin mismatches
- Example:
  - Product has FCC (USA cert) but claims China origin → ⚠️ Flag

### 5. **Price Reasonableness Check**
- Validates pricing against expected market prices for origin
- Premium origins (Switzerland, Germany) should have higher prices
- Budget origins (China, India) should have lower prices
- Detects unrealistic pricing that suggests counterfeits

### 6. **Category-Specific Rules**
- Electronics must come from known tech hubs
- Luxury items require high authenticity status
- Food/beverage accept broader origin ranges

## Verification Score (0-100)

Higher score = More trustworthy origin claim

**Scoring Algorithm:**
```
Score = 100 points (baseline)
  - 15 points per mismatch detected
  - 5 points per warning flag
  - Extra deductions for luxury/high-risk categories without proper documentation
```

**Score Interpretation:**
- **80-100**: ✓ Valid and trustworthy
- **60-79**: ℹ️ Valid but with minor concerns
- **40-59**: ⚠️ Suspicious, needs review
- **0-39**: 🚩 High risk, admin review required

## Usage Examples

### 1. Real-Time Validation During Product Creation

Vendors see instant feedback as they fill out product form:

```javascript
// On origin_country field blur
fetch('/api/validate-origin/', {
  method: 'POST',
  body: JSON.stringify({
    brand: 'Apple',
    origin_country: 'US',
    manufacturer: 'Foxconn',
    device_identifier_type: 'imei',
    price: '999.99',
    category_name: 'Electronics',
    authenticity_status: 'authentic'
  })
})
.then(r => r.json())
.then(result => {
  if (result.score < 40) {
    showWarning(result.reasoning);
  }
})
```

### 2. Batch Verification for Existing Products

```bash
# Check all products
python manage.py verify_product_origins

# Check only suspicious products
python manage.py verify_product_origins --suspicious-only

# Check specific vendor
python manage.py verify_product_origins --vendor-id=5

# Save results to database
python manage.py verify_product_origins --save-results
```

### 3. Programmatic Usage

```python
from core.origin_verification import verify_product_origin
from core.models import Product

product = Product.objects.get(id=123)
result = verify_product_origin(product)

if result['is_suspicious']:
    print(f"Verification score: {result['verification_score']}/100")
    print(f"Mismatches: {result['mismatches']}")
    # Flag for admin review
    product.status = 'PENDING_ADMIN_VERIFICATION'
    product.save()
```

## Example Scenarios

### Scenario 1: Legitimate Chinese Smartphone
```
Product: Xiaomi Mi 12
Claimed Origin: China
Brand: Xiaomi → Typically China ✓
Manufacturer: Xiaomi HQ, Beijing → China ✓
IMEI Prefix: 86 → China ✓
Certification: CCC (China requirement) ✓
Result: VALID (Score: 95/100)
```

### Scenario 2: Suspicious "European" Smartwatch
```
Product: "Luxury Swiss Watch"
Claimed Origin: Switzerland
Brand: Unknown → ⚠️ Flag
Certification: None provided → ⚠️ Flag
Authenticity: Unknown → ⚠️ Flag
Price: $49.99 (too low for Swiss watch) → ⚠️ Flag
Result: SUSPICIOUS (Score: 25/100)
Suggested Origin: China (likely counterfeit)
```

### Scenario 3: Valid Japanese Electronics
```
Product: Sony Camera
Claimed Origin: Japan
Brand: Sony → Typically Japan ✓
Manufacturer: Sony Corp, Tokyo → Japan ✓
Certification: Various Japan/International certs ✓
Authenticity: Authentic ✓
Result: VALID (Score: 92/100)
```

## Integration Points

### 1. Product Creation Form

Add AJAX validation to `vendor_product_form.html`:

```html
<script>
document.getElementById('id_origin_country').addEventListener('change', function() {
  validateOrigin();
});

async function validateOrigin() {
  const formData = new FormData();
  formData.append('brand', document.getElementById('id_brand').value);
  formData.append('origin_country', this.value);
  formData.append('manufacturer', document.getElementById('id_manufacturer').value);
  // ... add more fields
  
  const response = await fetch('{% url "core:ajax_validate_product_origin" %}', {
    method: 'POST',
    body: formData
  });
  const result = await response.json();
  displayVerificationResult(result);
}
</script>
```

### 2. Admin Dashboard

Show verification statistics:
- Suspicious origins pending review
- Verification trends by category
- Fraud patterns by vendor

### 3. Product Detail Page

Display verification badge to customers:
```
✓ Origin Verified: USA
Score: 88/100 - High confidence
```

## Configuration

Customize the engine in `origin_verification.py`:

```python
# Add custom brand-country mappings
BRAND_COUNTRY_MAP = {
    'your_brand': 'YOUR_COUNTRY_CODE',
    ...
}

# Adjust certification mappings
CERTIFICATION_COUNTRY_HINTS = {
    'your_cert': 'YOUR_COUNTRY_CODE',
    ...
}

# Modify verification score thresholds
SUSPICIOUS_THRESHOLD = 40  # Below this = suspicious
```

## Admin Commands

### View Suspicious Products

```bash
python manage.py verify_product_origins --suspicious-only
```

Output:
```
🚩 SUSPICIOUS: Fake Apple Watch (ID: 456)
   Vendor: TechReseller
   Claimed Origin: US
   Score: 28/100
   Reasoning: Origin verification detected 3 mismatch(es): 
   - Brand 'Apple' typically from US but vendor claims US;
   - Device identifier prefix suggests origin in China
   Suggested Origin: China
```

### Batch Export Results

```python
from core.origin_verification import verify_product_origin
from core.models import Product
import csv

suspicious = []
for product in Product.objects.filter(is_active=True):
    result = verify_product_origin(product)
    if result['is_suspicious']:
        suspicious.append({
            'product_id': product.id,
            'name': product.name,
            'score': result['verification_score'],
            'suggested_origin': result['suggested_origin']
        })

# Export to CSV for review
```

## Future Enhancements

1. **Machine Learning Integration**
   - Train ML model on historical fraud patterns
   - Predict likelihood of counterfeit based on multiple signals

2. **Supplier Verification**
   - Verify vendor's own origin claims
   - Cross-reference with business registration

3. **Blockchain Integration**
   - Store immutable verification records
   - Customer can verify authenticity on blockchain

4. **International Database Integration**
   - Real-time customs databases
   - Trademark registration verification
   - Manufacturer contact verification

5. **Computer Vision Analysis**
   - Analyze product images for authenticity markers
   - Detect counterfeit packaging

## API Reference

### `ajax_validate_product_origin`

**Endpoint:** `POST /api/validate-origin/`

**Input:**
```json
{
  "brand": "Apple",
  "manufacturer": "Foxconn",
  "origin_country": "US",
  "device_identifier_type": "imei",
  "device_identifier_value": "123456789012345",
  "certification_numbers": "FCC ID: ABC123",
  "price": "999.99",
  "product_type": "physical",
  "category_name": "Electronics",
  "authenticity_status": "authentic"
}
```

**Output:**
```json
{
  "valid": true,
  "score": 88,
  "confidence": 92.5,
  "reasoning": "Origin claim of US appears legitimate...",
  "severity": "info",
  "success_message": "✓ Origin claim verified"
}
```

### `ajax_get_origin_suggestions`

**Endpoint:** `POST /api/origin-suggestions/`

**Input:**
```json
{
  "brand": "Samsung",
  "category_name": "Electronics"
}
```

**Output:**
```json
{
  "similar_product_origins": [
    {"code": "KR", "name": "South Korea"},
    {"code": "CN", "name": "China"}
  ],
  "message": "Based on similar products in this category"
}
```

## Troubleshooting

**Q: My legitimate product keeps getting flagged as suspicious**
A: This might be because:
1. Brand isn't in the database - add it to `BRAND_COUNTRY_MAP`
2. Missing certifications - add them in the form
3. Unusual but valid combination - admin can override with verification

**Q: The verification score seems wrong**
A: Check the `_calculate_verification_score()` method. You can adjust:
- Mismatch penalty (-15 per mismatch)
- Flag penalty (-5 per flag)
- Category-specific adjustments

**Q: How do I add a new verification rule?**
A: Add a method like `_check_custom_rule()` in the `OriginVerificationEngine` class and call it from `verify_origin()`.

## Support

For issues or questions:
1. Check the logs: `/logs/origin_verification.log`
2. Run: `python manage.py verify_product_origins --product-id=<ID>`
3. Review: Review verification details in Django admin
