# Promotion Backend System - Quick Start Integration Guide

## What's Been Implemented

### ✅ Complete Backend System
- **4 New Django Models** with full database support
- **5 REST API ViewSets** with comprehensive endpoints
- **30+ API Endpoints** for promotions, variants, campaigns, codes
- **Custom Admin Interface** with advanced filtering and analytics
- **Production-Ready Migration** file

### ✅ Advanced Features
1. **A/B Testing (PromotionVariant)**
   - Test up to 3 variants per promotion
   - Track impressions, clicks, conversions
   - Calculate CTR, conversion rate, ROI
   - Mark winning variants
   - Auto-apply winning discount

2. **Customer Segmentation (PromotionSegmentRule)**
   - 6 pre-built segment types
   - Configurable eligibility rules
   - Automatic qualification checking
   - Per-segment performance tracking

3. **Bulk Code Generation (PromotionCode)**
   - Generate unlimited codes
   - Track redemption status
   - Export as CSV
   - Per-code analytics

4. **Campaign Management (PromotionCampaign)**
   - Group promotions under campaigns
   - Status workflow: draft → scheduled → active → paused → ended
   - Campaign-level performance metrics
   - Promotion breakdown reporting

---

## Quick Start Setup (5 minutes)

### Step 1: Run Migration
```bash
cd /path/to/Nexus
python manage.py migrate core 0088_promotion_backend_models
```

### Step 2: Register Admin
Add to `core/admin.py` (at the top):
```python
# Import all promotion admin classes
from core.promotion_admin import (
    PromotionVariantAdmin,
    PromotionSegmentRuleAdmin,
    PromotionCodeAdmin,
    PromotionCampaignAdmin,
)
```

### Step 3: Register URLs
Add to `core/urls.py` (in urlpatterns):
```python
path('promotions/', include('core.promotion_urls')),
```

### Step 4: Update Settings
```python
# settings.py

INSTALLED_APPS = [
    ...
    'rest_framework',
    'django_filters',
    ...
]

REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}
```

### Step 5: Test Migration
```bash
python manage.py shell
from core.models import PromotionVariant, PromotionCampaign
print("✓ Models loaded successfully")
```

---

## File Structure

### New Files Created
```
core/
├── promotion_views.py              (Functions-based views for campaign/analytics)
├── promotion_api_views.py          (DRF ViewSets for REST API)
├── promotion_serializers.py        (DRF Serializers)
├── promotion_admin.py              (Django admin configuration)
├── promotion_urls.py               (URL routing)
├── models.py                       (MODIFIED: Added 4 new models)
├── migrations/
│   └── 0088_promotion_backend_models.py (Database migration)
```

### Frontend Files (Already Complete)
```
templates/core/
├── vendor_promotion_list.html      (UI for list + suggestions)
├── vendor_promotion_form.html      (UI for form + variants + segments)
├── vendor_promotion_campaigns.html (Campaign management UI)
├── vendor_promotion_analytics.html (Analytics dashboard)
```

---

## New Models at a Glance

### PromotionVariant
**Purpose:** A/B testing promotions with different discount values

```python
# Create variant
variant = PromotionVariant.objects.create(
    promotion=promo,
    variant_type='B',  # A, B, or C
    discount_value=Decimal('25.00'),
    description='Test group'
)

# Track metrics
variant.impressions += 1
variant.clicks += 1
variant.conversions += 1
variant.revenue_generated += Decimal('123.45')
variant.save()

# Get analytics
print(f"CTR: {variant.ctr}%")
print(f"Conversion Rate: {variant.conversion_rate}%")
print(f"AVG Order Value: {variant.avg_order_value}")

# Mark winner
variant.is_winner = True
variant.save()
```

### PromotionSegmentRule
**Purpose:** Target specific customer segments

```python
# Create segment rule
rule = PromotionSegmentRule.objects.create(
    promotion=promo,
    segment_type='high_value',
    min_total_spent=Decimal('500.00'),
    min_orders_count=5
)

# Check if customer qualifies
qualifies = rule.qualifies_customer(user)
```

### PromotionCode
**Purpose:** Individual codes for bulk generation

```python
# Generate bulk codes
codes = [
    PromotionCode(promotion=promo, code=generate_code())
    for _ in range(1000)
]
PromotionCode.objects.bulk_create(codes)

# Redeem code
promo_code.redeem(user=customer, order=order)

# Get statistics
active = PromotionCode.objects.filter(promotion=promo, status='active').count()
redeemed = PromotionCode.objects.filter(promotion=promo, status='redeemed').count()
```

### PromotionCampaign
**Purpose:** Group and manage related promotions

```python
# Create campaign
campaign = PromotionCampaign.objects.create(
    vendor=vendor,
    name='Summer Sale 2024',
    start_date=datetime(2024, 6, 1),
    end_date=datetime(2024, 8, 31),
    emoji='☀️',
    status='draft'
)

# Add promotions
campaign.promotions.set([promo1, promo2, promo3])

# Get metrics
metrics = campaign.get_performance_metrics()
print(f"Total Revenue: {metrics['total_revenue']}")
print(f"Conversion Rate: {metrics['conversion_rate']}%")

# Check if active
if campaign.is_active_now:
    print("Campaign is running right now!")
```

---

## API Endpoints Quick Reference

### Promotions
```
GET    /api/promotions/promotions/                   # List
POST   /api/promotions/promotions/                   # Create
GET    /api/promotions/promotions/{id}/              # Detail
PATCH  /api/promotions/promotions/{id}/              # Update
DELETE /api/promotions/promotions/{id}/              # Delete
GET    /api/promotions/promotions/{id}/analytics/    # Get analytics
POST   /api/promotions/promotions/{id}/duplicate_with_new_dates/
```

### A/B Variants
```
GET    /api/promotions/variants/                     # List
POST   /api/promotions/variants/                     # Create
GET    /api/promotions/variants/{id}/                # Detail
POST   /api/promotions/variants/{id}/mark_winner/    # Mark winner
POST   /api/promotions/variants/{id}/record_impression/
POST   /api/promotions/variants/{id}/record_click/
POST   /api/promotions/variants/{id}/record_conversion/
```

### Campaigns
```
GET    /api/promotions/campaigns/                    # List
POST   /api/promotions/campaigns/                    # Create
GET    /api/promotions/campaigns/{id}/               # Detail
PATCH  /api/promotions/campaigns/{id}/               # Update
POST   /api/promotions/campaigns/{id}/activate/      # Activate
POST   /api/promotions/campaigns/{id}/pause/         # Pause
POST   /api/promotions/campaigns/{id}/end/           # End
GET    /api/promotions/campaigns/{id}/performance/   # Get metrics
GET    /api/promotions/campaigns/{id}/promotion_breakdown/
```

### Codes
```
GET    /api/promotions/codes/                        # List
POST   /api/promotions/codes/bulk_generate/          # Generate codes
GET    /api/promotions/codes/statistics/?promotion_id=1
POST   /api/promotions/codes/{id}/redeem/            # Redeem code
```

### Segments
```
GET    /api/promotions/segments/                     # List
POST   /api/promotions/segments/                     # Create
POST   /api/promotions/segments/check_eligibility/   # Check user
```

---

## Testing the APIs

### With Python
```python
import requests
import json

BASE_URL = 'http://localhost:8000/api/promotions'

# Create promotion
response = requests.post(
    f'{BASE_URL}/promotions/',
    json={
        'name': 'Test Promo',
        'code': 'TEST123',
        'promo_type': 'percentage',
        'discount_value': '20.00',
        'scope': 'all',
        'start_date': '2024-12-01T00:00:00Z',
        'end_date': '2024-12-31T23:59:59Z',
    },
    headers={'X-CSRFToken': csrf_token}
)
print(response.json())
```

### With Postman
1. Create collection: "Promotions API"
2. Set base URL: `http://localhost:8000/api/promotions`
3. Add requests:
   - GET /promotions/promotions/
   - POST /campaigns/
   - GET /codes/statistics/?promotion_id=1
   - etc.

### With cURL
```bash
# List promotions
curl http://localhost:8000/api/promotions/promotions/

# Generate codes
curl -X POST http://localhost:8000/api/promotions/codes/bulk_generate/ \
  -H "Content-Type: application/json" \
  -d '{"promotion_id": 1, "quantity": 100}'
```

---

## Frontend Integration Examples

### Apply Promotion to Cart
```javascript
// Check if customer is eligible
async function applyPromotion(promotionCode, cartTotal) {
  const response = await fetch('/api/promotions/promotions/', {
    method: 'GET',
    headers: { 'Authorization': `Bearer ${token}` }
  });
  
  const promos = await response.json();
  const promo = promos.results.find(p => p.code === promotionCode);
  
  if (!promo) {
    alert('Promotion not found');
    return;
  }
  
  if (promo.minimum_purchase_amount && cartTotal < promo.minimum_purchase_amount) {
    alert(`Minimum purchase: ${promo.minimum_purchase_amount}`);
    return;
  }
  
  // Calculate discount
  const discount = promo.promo_type === 'percentage'
    ? (cartTotal * promo.discount_value) / 100
    : promo.discount_value;
  
  updateCart({ discount, promotionId: promo.id });
}
```

### Display A/B Test
```javascript
// Select random variant
async function getVariant(promotionId) {
  const response = await fetch(
    `/api/promotions/promotions/${promotionId}/`
  );
  const promo = await response.json();
  
  const variant = promo.variants[
    Math.random() < 0.5 ? 0 : 1
  ];
  
  // Record impression
  fetch(
    `/api/promotions/variants/${variant.id}/record_impression/`,
    { method: 'POST' }
  );
  
  return variant;
}
```

### Track Conversion
```javascript
// After order placed
async function trackPromoConversion(variantId, orderId, revenue) {
  const response = await fetch(
    `/api/promotions/variants/${variantId}/record_conversion/`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ order_id: orderId, revenue: revenue })
    }
  );
  
  console.log('Conversion tracked:', await response.json());
}
```

---

## Admin Interface Features

### PromotionVariant Admin
- **Dashboard:** Variant type, performance metrics, winner status
- **Filters:** By type (A/B/C), winner status, promotion
- **Quick Stats:** Impressions, conversions, revenue, conversion rate
- **Actions:** Mark as winner

### PromotionCode Admin
- **Dashboard:** Code, status (active/redeemed/disabled), redeemed user
- **Filters:** By status, promotion, redemption date
- **Bulk Actions:** Mark as redeemed, disable codes, export list
- **Quick Stats:** Redemption rate, status counts

### PromotionCampaign Admin
- **Dashboard:** Campaign name with emoji, status, performance
- **Filters:** By status (draft/active/ended), vendor, date range
- **Quick Stats:** Number of promotions, revenue generated
- **Performance:** Total conversions, conversion rate, ROI

### PromotionSegmentRule Admin
- **Dashboard:** Promotion, segment type, active status
- **Conditions:** Min spending, order count, geographic rules
- **Filters:** By segment type, activity status

---

## Common Tasks

### Task 1: Create A/B Test Campaign
```python
from core.models import Promotion, PromotionVariant, PromotionCampaign

# Get promotion
promo = Promotion.objects.get(id=1)

# Create 2 variants
variant_a = PromotionVariant.objects.create(
    promotion=promo,
    variant_type='A',
    discount_value=Decimal('20.00'),
    description='Control: 20% discount'
)

variant_b = PromotionVariant.objects.create(
    promotion=promo,
    variant_type='B',
    discount_value=Decimal('25.00'),
    description='Test: 25% discount'
)

# Create campaign
campaign = PromotionCampaign.objects.create(
    vendor=promo.applicable_vendor,
    name='Flash Sale A/B Test',
    start_date=timezone.now(),
    end_date=timezone.now() + timedelta(days=7),
    status='active'
)
campaign.promotions.add(promo)
```

### Task 2: Target High-Value Customers
```python
from core.models import PromotionSegmentRule

rule = PromotionSegmentRule.objects.create(
    promotion=promo,
    segment_type='high_value',
    min_total_spent=Decimal('500.00'),
    min_orders_count=3,
    is_active=True
)

# Check eligibility
if rule.qualifies_customer(user):
    apply_exclusive_discount(user, promo)
```

### Task 3: Generate and Track Codes
```python
from core.models import PromotionCode
import secrets, string

# Generate 500 codes
codes = []
charset = string.ascii_uppercase + string.digits
for _ in range(500):
    while True:
        code = ''.join(secrets.choice(charset) for _ in range(10))
        if not PromotionCode.objects.filter(code=code).exists():
            break
    codes.append(PromotionCode(promotion=promo, code=code))

PromotionCode.objects.bulk_create(codes)

# Track redemptions
stats = PromotionCode.objects.filter(promotion=promo).aggregate(
    total=Count('id'),
    redeemed=Count('id', filter=Q(status='redeemed')),
)
print(f"Redemption Rate: {stats['redeemed']/stats['total']*100}%")
```

---

## Performance Considerations

### Database Optimization
- All ForeignKey fields have automatic indexes
- M2M queries use select_related/prefetch_related where needed
- Aggregation queries use Sum/Avg for efficiency

### Caching Strategy
```python
# Cache campaign list for 5 minutes
from django.views.decorators.cache import cache_page

@cache_page(60 * 5)
def list_campaigns(request):
    ...
```

### Pagination
All list endpoints support pagination:
```
GET /api/promotions/promotions/?page=1&page_size=25
```

---

## Troubleshooting

### Error: "Migration not applied"
```bash
python manage.py migrate core 0088_promotion_backend_models
python manage.py migrate core
```

### Error: "No module named 'django_filters'"
```bash
pip install django-filter
```

### Error: "404 Not Found" on API
1. Check URL routing in `core/urls.py`
2. Verify `include('core.promotion_urls')` is added
3. Test: `curl http://localhost:8000/api/promotions/promotions/`

### Error: "Permission denied" (403)
- User must be logged in
- Check DRF permissions in `settings.py`
- Test with authentication token/session

---

## Next Steps for Your App

1. **Frontend:** Connect Vue components to API endpoints
2. **Checkout:** Integrate promotion application logic
3. **Email:** Send promotional codes to eligible customers
4. **Dashboard:** Real-time analytics visualization
5. **Reporting:** Export analytics to PDF/Excel
6. **Webhooks:** Send events to external systems
7. **ML:** Predict optimal discount values using historical data

---

## Support Files

- **Full API Documentation:** `PROMOTION_BACKEND_API_DOCUMENTATION.md`
- **Admin Interface:** `core/promotion_admin.py`
- **REST ViewSets:** `core/promotion_api_views.py`
- **Database Models:** `core/models.py` (PromotionVariant, PromotionSegmentRule, PromotionCode, PromotionCampaign)
- **Models File:** `PROMOTION_BACKEND_MODELS_REFERENCE.md`

---

## Success Checklist

- [ ] Migration run successfully
- [ ] Admin interface shows 4 new models
- [ ] API endpoints return 200 status
- [ ] Can create promotion with variants
- [ ] Can generate bulk codes
- [ ] Can create campaigns
- [ ] Frontend forms submit correctly
- [ ] Analytics data displays properly

**You're all set!** 🚀
