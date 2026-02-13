# Promotion Backend Integration - Complete API Documentation

## Overview

This document provides complete documentation for the promotion backend system, including A/B testing, customer segmentation, bulk code generation, campaign management, and analytics.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                   Frontend (Vue/Vanilla JS)                      │
├─────────────────────────────────────────────────────────────────┤
│        vendor_promotion_list.html  │  vendor_promotion_form.html │
│        vendor_promotion_campaigns.html  │  vendor_promotion_analytics.html │
├─────────────────────────────────────────────────────────────────┤
│              REST API Endpoints (JSON)                            │
├─────────────────────────────────────────────────────────────────┤
│          Django ViewSets (promotion_api_views.py)                 │
│  PromotionViewSet  │  VariantViewSet  │  CampaignViewSet  │ ... │
├─────────────────────────────────────────────────────────────────┤
│              Django Models (models.py)                            │
│  Promotion  │  PromotionVariant  │  PromotionCampaign  │ ...    │
├─────────────────────────────────────────────────────────────────┤
│                    Database (SQLite)                              │
└─────────────────────────────────────────────────────────────────┘
```

---

## Database Models

### 1. PromotionVariant (A/B Testing)
Represents different variants of a promotion for A/B testing.

**Fields:**
- `id`: Auto-generated ID
- `promotion`: FK to Promotion
- `variant_type`: CharField (A, B, or C)
- `discount_value`: Variant-specific discount
- `description`: Optional description
- `impressions`: Number of times shown
- `clicks`: Number of times clicked
- `conversions`: Number of successful conversions
- `revenue_generated`: Total revenue from this variant
- `is_winner`: Boolean flag for winning variant
- `created_at`: Timestamp

**Unique Constraint:** `(promotion, variant_type)`

**Methods:**
- `ctr()`: Click-through rate percentage
- `conversion_rate()`: Conversion rate percentage
- `avg_order_value()`: Average revenue per conversion

---

### 2. PromotionSegmentRule (Customer Segmentation)
Defines rules for targeting specific customer segments.

**Fields:**
- `id`: Auto-generated ID
- `promotion`: FK to Promotion
- `segment_type`: CharField with choices:
  - `new_customers`: First-time buyers only
  - `loyalty_members`: Existing loyalty program members
  - `abandoned_cart`: Cart recovery targets
  - `high_value`: Customers with high lifetime value
  - `geographic`: Location-based targeting
  - `first_time`: Never purchased before
- `min_total_spent`: Decimal (optional) - minimum lifetime spending
- `min_orders_count`: Integer (optional) - minimum order count
- `days_since_last_order`: Integer (optional) - re-engagement window
- `country_codes`: String (comma-separated)
- `is_active`: Boolean
- `created_at`: Timestamp

**Unique Constraint:** `(promotion, segment_type)`

**Methods:**
- `qualifies_customer(user)`: Check if user qualifies for segment

---

### 3. PromotionCode (Bulk Code Generation)
Individual codes for bulk-generated promotions.

**Fields:**
- `id`: Auto-generated ID
- `promotion`: FK to Promotion
- `code`: Unique code string
- `status`: CharField with choices: active, redeemed, expired, disabled
- `redeemed_by`: FK to User (optional)
- `redeemed_at`: Timestamp (optional)
- `redeemed_order`: FK to Order (optional)
- `created_at`: Timestamp
- `updated_at`: Timestamp

**Indexes:**
- `(promotion, status)`
- `code`

**Methods:**
- `redeem(user, order)`: Mark code as redeemed

---

### 4. PromotionCampaign (Campaign Grouping)
Groups related promotions under a campaign for coordinated management.

**Fields:**
- `id`: Auto-generated ID
- `vendor`: FK to Vendor
- `name`: Campaign name
- `description`: Campaign description
- `promotions`: M2M to Promotion
- `start_date`: DateTime
- `end_date`: DateTime
- `status`: CharField with choices: draft, scheduled, active, paused, ended
- `emoji`: Unicode emoji for UI
- `impressions`: Read-only, aggregated
- `clicks`: Read-only, aggregated
- `revenue_generated`: Read-only, aggregated
- `created_at`: Timestamp
- `updated_at`: Timestamp

**Indexes:**
- `(vendor, status)`
- `(start_date, end_date)`

**Methods:**
- `is_active_now`: Property checking if currently active
- `promotion_count`: Count of grouped promotions
- `get_performance_metrics()`: Aggregated performance data

---

## REST API Endpoints

### Base URL
```
/api/promotions/
```

### Authentication
All endpoints require `IsAuthenticated` permission. Include session cookie or token.

---

### Promotions API

#### List Promotions
```http
GET /api/promotions/promotions/
```

**Query Parameters:**
- `is_active`: Boolean filter
- `scope`: all, category, product, vendor
- `promo_type`: percentage, fixed_amount
- `search`: Search by name, code, description
- `ordering`: created_at, start_date, usage_count
- `page`: Pagination (default 10 per page)

**Response:**
```json
{
  "count": 5,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "name": "Summer Sale 20%",
      "code": "SUMMER20",
      "promo_type": "percentage",
      "discount_value": "20.00",
      "scope": "all",
      "start_date": "2024-06-01T00:00:00Z",
      "end_date": "2024-08-31T23:59:59Z",
      "usage_limit": 1000,
      "usage_count": 245,
      "is_active": true,
      "variant_count": 2,
      "active_variant_count": 1,
      "created_at": "2024-05-15T10:30:00Z"
    }
  ]
}
```

#### Get Promotion Detail
```http
GET /api/promotions/promotions/{id}/
```

**Response:**
```json
{
  "id": 1,
  "name": "Summer Sale 20%",
  "description": "Company-wide summer promotional campaign",
  "code": "SUMMER20",
  "promo_type": "percentage",
  "discount_value": "20.00",
  "scope": "all",
  "applicable_categories": [1, 2, 3],
  "applicable_products": [5, 10, 15],
  "applicable_vendor": 1,
  "start_date": "2024-06-01T00:00:00Z",
  "end_date": "2024-08-31T23:59:59Z",
  "minimum_purchase_amount": "50.00",
  "usage_limit": 1000,
  "usage_count": 245,
  "uses_per_customer": 5,
  "is_active": true,
  "variants": [
    {
      "id": 1,
      "variant_type": "A",
      "discount_value": "20.00",
      "description": "Control group",
      "impressions": 1000,
      "clicks": 150,
      "conversions": 75,
      "revenue_generated": "6000.00",
      "ctr": 15.0,
      "conversion_rate": 50.0,
      "avg_order_value": 80.0,
      "is_winner": false
    }
  ],
  "segment_rules": [...],
  "codes_count": 500,
  "codes_redeemed": 245,
  "created_at": "2024-05-15T10:30:00Z"
}
```

#### Create Promotion
```http
POST /api/promotions/promotions/
Content-Type: application/json

{
  "name": "Flash Sale",
  "description": "2-hour flash sale",
  "code": "FLASH50",
  "promo_type": "percentage",
  "discount_value": "50.00",
  "scope": "all",
  "start_date": "2024-12-01T00:00:00Z",
  "end_date": "2024-12-01T02:00:00Z",
  "minimum_purchase_amount": "100.00",
  "usage_limit": 50,
  "uses_per_customer": 1
}
```

#### Update Promotion
```http
PATCH /api/promotions/promotions/{id}/
Content-Type: application/json

{
  "discount_value": "25.00",
  "is_active": false
}
```

#### Get Promotion Analytics
```http
GET /api/promotions/promotions/{id}/analytics/
```

**Response:**
```json
{
  "promotion_id": 1,
  "promotion_name": "Summer Sale 20%",
  "total_variants": 2,
  "total_revenue": 12000.00,
  "total_conversions": 150,
  "total_clicks": 300,
  "total_impressions": 2000,
  "avg_conversion_rate": 50.0,
  "codes_generated": 500,
  "codes_redeemed": 245
}
```

#### Duplicate Promotion
```http
POST /api/promotions/promotions/{id}/duplicate_with_new_dates/
Content-Type: application/json

{
  "start_date": "2024-07-01T00:00:00Z",
  "end_date": "2024-09-30T23:59:59Z"
}
```

---

### A/B Testing / Variants API

#### List Variants
```http
GET /api/promotions/variants/
```

**Query Parameters:**
- `promotion`: Filter by promotion ID
- `is_winner`: Filter by winner status
- `ordering`: created_at

#### Get Variant Detail
```http
GET /api/promotions/variants/{id}/
```

#### Create Variant
```http
POST /api/promotions/variants/
Content-Type: application/json

{
  "promotion": 1,
  "variant_type": "B",
  "discount_value": "25.00",
  "description": "Test group with lower discount"
}
```

#### Mark Variant as Winner
```http
POST /api/promotions/variants/{id}/mark_winner/
```

**Response:**
```json
{
  "detail": "Variant marked as winner",
  "variant": {
    "id": 2,
    "variant_type": "B",
    "discount_value": "25.00",
    "is_winner": true,
    ...
  }
}
```

#### Record Impression
```http
POST /api/promotions/variants/{id}/record_impression/
```

**Response:**
```json
{
  "impressions": 1001
}
```

#### Record Click
```http
POST /api/promotions/variants/{id}/record_click/
```

#### Record Conversion
```http
POST /api/promotions/variants/{id}/record_conversion/
Content-Type: application/json

{
  "order_id": 123,
  "revenue": 85.50
}
```

---

### Promotion Codes API

#### List Codes
```http
GET /api/promotions/codes/
```

**Query Parameters:**
- `promotion`: Filter by promotion ID
- `status`: active, redeemed, expired, disabled
- `search`: Search by code
- `page`: Pagination

#### Get Code Statistics
```http
GET /api/promotions/codes/statistics/?promotion_id=1
```

**Response:**
```json
{
  "total_codes": 500,
  "active_codes": 255,
  "redeemed_codes": 245,
  "disabled_codes": 0,
  "expired_codes": 0,
  "redemption_rate": 49.0
}
```

#### Generate Bulk Codes
```http
POST /api/promotions/codes/bulk_generate/
Content-Type: application/json

{
  "promotion_id": 1,
  "quantity": 1000
}
```

**Response:**
```json
{
  "success": true,
  "quantity_created": 1000,
  "message": "1000 codes generated successfully",
  "codes_sample": ["ABC123DEF4", "XYZ789QWE0", ...]
}
```

#### Redeem Code
```http
POST /api/promotions/codes/{id}/redeem/
Content-Type: application/json

{
  "order_id": 123
}
```

---

### Customer Segmentation API

#### List Segment Rules
```http
GET /api/promotions/segments/
```

#### Create Segment Rule
```http
POST /api/promotions/segments/
Content-Type: application/json

{
  "promotion": 1,
  "segment_type": "high_value",
  "min_total_spent": "500.00",
  "min_orders_count": 5,
  "is_active": true
}
```

#### Check User Eligibility
```http
POST /api/promotions/segments/check_eligibility/
Content-Type: application/json

{
  "promotion_id": 1
}
```

**Response:**
```json
{
  "promotion_id": 1,
  "user_id": 42,
  "eligible_segments": ["High Value Customers", "Loyalty Program Members"],
  "is_eligible": true
}
```

---

### Campaign Management API

#### List Campaigns
```http
GET /api/promotions/campaigns/
```

**Query Parameters:**
- `status`: draft, scheduled, active, paused, ended
- `search`: Campaign name
- `page`: Pagination

#### Get Campaign Detail
```http
GET /api/promotions/campaigns/{id}/
```

#### Create Campaign
```http
POST /api/promotions/campaigns/
Content-Type: application/json

{
  "name": "Summer Mega Sale",
  "description": "3-month summer promotional campaign",
  "start_date": "2024-06-01T00:00:00Z",
  "end_date": "2024-08-31T23:59:59Z",
  "emoji": "☀️",
  "status": "draft",
  "promotions": [1, 2, 3]
}
```

#### Activate Campaign
```http
POST /api/promotions/campaigns/{id}/activate/
```

#### Pause Campaign
```http
POST /api/promotions/campaigns/{id}/pause/
```

#### End Campaign
```http
POST /api/promotions/campaigns/{id}/end/
```

#### Get Campaign Performance
```http
GET /api/promotions/campaigns/{id}/performance/
```

**Response:**
```json
{
  "campaign_id": 1,
  "campaign_name": "Summer Mega Sale",
  "metrics": {
    "total_impressions": 5000,
    "total_clicks": 750,
    "total_conversions": 200,
    "total_revenue": 18500.00,
    "conversion_rate": 26.67
  },
  "performance_summary": {
    "status": "high",
    "roi_estimate": 92.5
  }
}
```

#### Get Promotion Breakdown
```http
GET /api/promotions/campaigns/{id}/promotion_breakdown/
```

**Response:**
```json
[
  {
    "promotion_id": 1,
    "promotion_name": "20% Flash Sale",
    "promotion_code": "FLASH20",
    "variant_count": 2,
    "revenue": 6000.00,
    "conversions": 75,
    "roi": 80.0
  },
  ...
]
```

---

## Frontend Integration Examples

### 1. Create A/B Variant
```javascript
async function createVariant() {
  const response = await fetch('/api/promotions/variants/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCookie('csrftoken'),
    },
    body: JSON.stringify({
      promotion: promotionId,
      variant_type: 'B',
      discount_value: '25.00',
      description: 'Test variant'
    })
  });
  
  const data = await response.json();
  console.log('Created variant:', data);
}
```

### 2. Record Analytics Events
```javascript
// When promotion is shown to customer
async function recordImpression(variantId) {
  await fetch(`/api/promotions/variants/${variantId}/record_impression/`, {
    method: 'POST',
    headers: {
      'X-CSRFToken': getCookie('csrftoken'),
    }
  });
}

// When customer applies promotion
async function recordConversion(variantId, orderId, revenue) {
  await fetch(`/api/promotions/variants/${variantId}/record_conversion/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCookie('csrftoken'),
    },
    body: JSON.stringify({
      order_id: orderId,
      revenue: revenue
    })
  });
}
```

### 3. Check Customer Segment Eligibility
```javascript
async function checkEligibility(promotionId) {
  const response = await fetch('/api/promotions/segments/check_eligibility/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCookie('csrftoken'),
    },
    body: JSON.stringify({
      promotion_id: promotionId
    })
  });
  
  const data = await response.json();
  if (data.is_eligible) {
    console.log('Customer qualifies for:', data.eligible_segments);
    applyPromotion();
  }
}
```

### 4. Generate and Export Bulk Codes
```javascript
async function generateBulkCodes(promotionId, quantity) {
  const response = await fetch('/api/promotions/codes/bulk_generate/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCookie('csrftoken'),
    },
    body: JSON.stringify({
      promotion_id: promotionId,
      quantity: quantity
    })
  });
  
  const data = await response.json();
  console.log(`Generated ${data.quantity_created} codes`);
  
  // Download CSV
  window.location.href = `/promotions/codes/export/${promotionId}/`;
}
```

---

## Migration and Setup

### 1. Run Migration
```bash
python manage.py migrate core 0088_promotion_backend_models
```

### 2. Register Admin
Add to `core/admin.py`:
```python
from core.promotion_admin import *
```

### 3. Register URLs
Add to `core/urls.py`:
```python
path('promotions/', include('core.promotion_urls')),
```

### 4. Install REST Framework (if not already)
```bash
pip install djangorestframework
```

### 5. Configure Settings
```python
# settings.py
INSTALLED_APPS = [
    ...
    'rest_framework',
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
}
```

---

## Testing with cURL

### Test 1: Create Promotion
```bash
curl -X POST http://localhost:8000/api/promotions/promotions/ \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: <token>" \
  -d '{
    "name": "Test Promotion",
    "code": "TEST123",
    "promo_type": "percentage",
    "discount_value": "20.00",
    "scope": "all",
    "start_date": "2024-12-01T00:00:00Z",
    "end_date": "2024-12-31T23:59:59Z"
  }'
```

### Test 2: Generate Codes
```bash
curl -X POST http://localhost:8000/api/promotions/codes/bulk_generate/ \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: <token>" \
  -d '{
    "promotion_id": 1,
    "quantity": 100
  }'
```

---

## Performance Optimization

### Database Indexes
All foreign keys and frequently queried fields have automatic indexes:
- `PromotionCode`: `(promotion, status)`, `code`
- `PromotionCampaign`: `(vendor, status)`, `(start_date, end_date)`

### Caching Recommendations
```python
from django.views.decorators.cache import cache_page

@cache_page(5 * 60)  # Cache for 5 minutes
def get_promotion_analytics(request, promotion_id):
    ...
```

### Pagination
All list endpoints support pagination (default 10 per page):
```
GET /api/promotions/promotions/?page=2&page_size=50
```

---

## Error Handling

### 400 Bad Request
```json
{
  "error": "Invalid status",
  "detail": "Status must be one of: draft, scheduled, active, paused, ended"
}
```

### 403 Forbidden
```json
{
  "error": "Permission denied",
  "detail": "You do not have permission to modify this resource"
}
```

### 404 Not Found
```json
{
  "detail": "Not found"
}
```

---

## Next Steps

1. **Frontend Integration**: Connect Vue/JavaScript forms to APIs
2. **Analytics Dashboard**: Build real-time metrics visualization
3. **Email Notifications**: Send promotion alerts to qualified customers
4. **SMS Campaigns**: Auto SMS for high-value customers
5. **Advanced Reporting**: Export analytics to PDF/Excel
6. **Machine Learning**: Predict optimal discount values
7. **Webhook Events**: Send events to external systems

---

## Support

For issues or questions:
1. Check Django admin interface for data integrity
2. Review API response status codes
3. Check server logs: `tail -f logs/django.log`
4. Test endpoints with Postman or cURL
