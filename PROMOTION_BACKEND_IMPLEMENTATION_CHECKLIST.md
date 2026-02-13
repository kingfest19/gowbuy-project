# Promotion Backend - Implementation Checklist

## ✅ Phase 1: Setup (Estimated Time: 15 minutes)

### Database & Dependencies
- [ ] **Install REST Framework**
  ```bash
  pip install djangorestframework django-filter
  ```
  
- [ ] **Run Migration**
  ```bash
  python manage.py migrate core 0088_promotion_backend_models
  ```
  
- [ ] **Verify Models Created**
  ```bash
  python manage.py shell
  from core.models import PromotionVariant, PromotionCampaign
  print("✓ Models imported successfully")
  ```

### Django Configuration
- [ ] **Add to settings.py**
  ```python
  INSTALLED_APPS = [
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

- [ ] **Register URLs in core/urls.py**
  ```python
  urlpatterns = [
      ...
      path('promotions/', include('core.promotion_urls')),
      ...
  ]
  ```

- [ ] **Register Admin in core/admin.py**
  ```python
  from core.promotion_admin import *
  ```

### Test Setup
- [ ] **Start Development Server**
  ```bash
  python manage.py runserver
  ```

- [ ] **Access Django Admin**
  ```
  http://localhost:8000/admin/core/
  ```

- [ ] **Verify 4 New Models Appear**
  - PromotionVariants
  - PromotionSegmentRules
  - PromotionCodes
  - PromotionCampaigns

---

## ✅ Phase 2: API Testing (Estimated Time: 20 minutes)

### Test API Endpoints

#### ✓ Test 1: Create Promotion
```bash
curl -X POST http://localhost:8000/api/promotions/promotions/ \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: <your-csrf-token>" \
  -d '{
    "name": "Test Flash Sale",
    "code": "FLASH50",
    "promo_type": "percentage",
    "discount_value": "50",
    "scope": "all",
    "start_date": "2024-12-01T00:00:00Z",
    "end_date": "2024-12-31T23:59:59Z",
    "minimum_purchase_amount": "100"
  }'
```
- [ ] Returns 201 Created
- [ ] Response includes `id`, `name`, `code`

#### ✓ Test 2: List Promotions
```bash
curl http://localhost:8000/api/promotions/promotions/
```
- [ ] Returns 200 OK
- [ ] Response includes pagination

#### ✓ Test 3: Create A/B Variant
```bash
curl -X POST http://localhost:8000/api/promotions/variants/ \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: <token>" \
  -d '{
    "promotion": 1,
    "variant_type": "B",
    "discount_value": "45",
    "description": "Test variant"
  }'
```
- [ ] Returns 201 Created
- [ ] Variant created successfully

#### ✓ Test 4: Generate Bulk Codes
```bash
curl -X POST http://localhost:8000/api/promotions/codes/bulk_generate/ \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: <token>" \
  -d '{
    "promotion_id": 1,
    "quantity": 100
  }'
```
- [ ] Returns 201 Created
- [ ] 100 codes generated

#### ✓ Test 5: Create Campaign
```bash
curl -X POST http://localhost:8000/api/promotions/campaigns/ \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: <token>" \
  -d '{
    "name": "Summer Sale 2024",
    "start_date": "2024-06-01T00:00:00Z",
    "end_date": "2024-08-31T23:59:59Z",
    "emoji": "☀️",
    "promotions": [1]
  }'
```
- [ ] Returns 201 Created
- [ ] Campaign created with promotions

---

## ✅ Phase 3: Admin Interface Testing (Estimated Time: 15 minutes)

### Test Admin Features

#### Promotion Variant Admin
- [ ] Navigate to `/admin/core/promotionvariant/`
- [ ] **Create** a variant
  - [ ] Select promotion
  - [ ] Choose variant type (A, B, C)
  - [ ] Enter discount value
  - [ ] Add description
  - [ ] Save
- [ ] **View** variant
  - [ ] See performance metrics (impressions, clicks, conversions)
  - [ ] Check CTR and conversion rate
  - [ ] See revenue generated
- [ ] **Filter** variants
  - [ ] By variant type
  - [ ] By promotion
  - [ ] By winner status
- [ ] **Mark Winner**
  - [ ] Select variant
  - [ ] Click "Mark as winner"
  - [ ] Verify promotion updated

#### Promotion Code Admin
- [ ] Navigate to `/admin/core/promotioncode/`
- [ ] **Create** codes (bulk)
  - [ ] See list of generated codes
  - [ ] Check status (active/redeemed/disabled)
- [ ] **Filter** codes
  - [ ] By status
  - [ ] By promotion
  - [ ] By redemption date
- [ ] **Bulk Actions**
  - [ ] Mark multiple as redeemed
  - [ ] Bulk disable codes
  - [ ] Export list

#### Promotion Campaign Admin
- [ ] Navigate to `/admin/core/promotioncampaign/`
- [ ] **Create** campaign
  - [ ] Enter campaign name
  - [ ] Add emoji
  - [ ] Set date range
  - [ ] Add promotions
  - [ ] Set status to "scheduled"
  - [ ] Save
- [ ] **View** campaign
  - [ ] See performance metrics
  - [ ] Check status badge color
  - [ ] View promotion count
  - [ ] See revenue generated
- [ ] **Update** status
  - [ ] Change from scheduled to active
  - [ ] Change from active to paused
  - [ ] Change from active to ended

#### Segment Rule Admin
- [ ] Navigate to `/admin/core/promotionsegmentrule/`
- [ ] **Create** segment rule
  - [ ] Select promotion
  - [ ] Choose segment type
  - [ ] Set conditions
  - [ ] Save
- [ ] **View** rules
  - [ ] See conditions applied
  - [ ] Check if active

---

## ✅ Phase 4: Utility Functions Testing (Estimated Time: 10 minutes)

### Test Helper Functions

#### A/B Testing Helpers
- [ ] **Create A/B Test**
  ```python
  from core.promotion_utils import create_ab_test
  promo = Promotion.objects.get(id=1)
  v_a, v_b = create_ab_test(promo, Decimal('25.00'))
  assert v_a.variant_type == 'A'
  assert v_b.variant_type == 'B'
  ```

- [ ] **Determine Winner**
  ```python
  from core.promotion_utils import determine_winner
  winner = determine_winner(promo)
  assert winner.is_winner == True
  ```

- [ ] **Get Performance**
  ```python
  from core.promotion_utils import get_variant_performance
  perf = get_variant_performance(promo)
  assert 'A' in perf
  assert 'ctr' in perf['A']
  ```

#### Code Generation Helpers
- [ ] **Generate Codes**
  ```python
  from core.promotion_utils import generate_bulk_codes
  codes = generate_bulk_codes(promo, 500, prefix='SUM')
  assert len(codes) == 500
  assert codes[0].code.startswith('SUM')
  ```

- [ ] **Get Statistics**
  ```python
  from core.promotion_utils import get_codes_statistics
  stats = get_codes_statistics(promo)
  assert 'total_codes' in stats
  assert 'redemption_rate' in stats
  ```

#### Campaign Helpers
- [ ] **Create Campaign**
  ```python
  from core.promotion_utils import create_campaign
  campaign = create_campaign(vendor, 'Test', [promo], start, end)
  assert campaign.name == 'Test'
  ```

- [ ] **Get Active Campaigns**
  ```python
  from core.promotion_utils import get_active_campaigns
  active = get_active_campaigns(vendor)
  assert active.count() >= 0
  ```

#### Analytics Helpers
- [ ] **Get ROI**
  ```python
  from core.promotion_utils import get_promotion_roi
  roi = get_promotion_roi(promo)
  assert 'roi_percentage' in roi
  assert 'total_revenue' in roi
  ```

- [ ] **Get Recommendations**
  ```python
  from core.promotion_utils import get_smart_recommendations
  recs = get_smart_recommendations(vendor)
  assert isinstance(recs, list)
  assert len(recs) > 0
  ```

---

## ✅ Phase 5: Frontend Integration (Estimated Time: Ongoing)

### Connect Frontend to APIs

#### Promotion List Page
- [ ] [ ] API works with form submission
- [ ] [ ] Filters (active, status, search)
- [ ] [ ] Pagination working
- [ ] [ ] Create button functional
- [ ] [ ] Edit button functional
- [ ] [ ] Delete button functional

#### Promotion Form Page
- [ ] [ ] Form submits to API
- [ ] [ ] Preview updates in real-time
- [ ] [ ] A/B Testing section working
  - [ ] [ ] Enable toggle functional
  - [ ] [ ] Variant value updates
  - [ ] [ ] Preview shows variants
- [ ] [ ] Segment section working
  - [ ] [ ] Checkboxes update preview
  - [ ] [ ] Audience display correct
- [ ] [ ] Save button creates/updates

#### Campaign Page
- [ ] [ ] Create campaign form works
- [ ] [ ] Campaign list displays correctly
- [ ] [ ] Status changes work
- [ ] [ ] Performance metrics display
- [ ] [ ] Archive/delete functional

#### Analytics Page
- [ ] [ ] Charts load with mock data
- [ ] [ ] Statistics cards display
- [ ] [ ] Trend data displays
- [ ] [ ] Recommendations show up

---

## ✅ Phase 6: Production Preparation (Estimated Time: 10 minutes)

### Security & Performance

#### Database
- [ ] [ ] Run `python manage.py check`
- [ ] [ ] Run `python manage.py makemigrations --dry-run` (should show no changes)
- [ ] [ ] Database file size reasonable (<100MB)

#### Performance
- [ ] [ ] Test with 1000+ promotions
- [ ] [ ] Test with 10000+ codes
- [ ] [ ] Response time < 1 second
- [ ] [ ] Pagination working at scale

#### Security
- [ ] [ ] All endpoints require authentication
- [ ] [ ] CSRF protection working
- [ ] [ ] SQL injection prevention (ORM used)
- [ ] [ ] Unauthorized access blocked

#### Documentation
- [ ] [ ] **PROMOTION_BACKEND_API_DOCUMENTATION.md** reviewed
- [ ] [ ] **PROMOTION_BACKEND_QUICK_START.md** reviewed
- [ ] [ ] **PROMOTION_BACKEND_IMPLEMENTATION_COMPLETE.md** reviewed
- [ ] [ ] **core/promotion_utils.py** reviewed

---

## ✅ Phase 7: Deployment (Estimated Time: 5 minutes)

### Pre-Deployment Checklist

#### Django Settings
- [ ] [ ] DEBUG = False in production
- [ ] [ ] SECRET_KEY stored in environment variable
- [ ] [ ] ALLOWED_HOSTS configured
- [ ] [ ] CSRF settings correct

#### Database
- [ ] [ ] Migration files committed to git
- [ ] [ ] Backup of database taken
- [ ] [ ] Migration order verified

#### Static Files
- [ ] [ ] Media folder accessible
- [ ] [ ] Admin CSS/JS loading correctly

#### Testing
- [ ] [ ] All API endpoints tested
- [ ] [ ] Admin interface working
- [ ] [ ] No console errors
- [ ] [ ] Performance acceptable

---

## 🔄 Ongoing Maintenance

### Weekly Tasks
- [ ] Check promotion performance dashboards
- [ ] Review low-performing promotions
- [ ] Export and archive old campaigns
- [ ] Clean up disabled codes

### Monthly Tasks
- [ ] Archive ended campaigns
- [ ] Analyze promotion ROI
- [ ] Update segment rules if needed
- [ ] Plan next promotions

### Quarterly Tasks
- [ ] Review all A/B test results
- [ ] Optimize discount strategies
- [ ] Plan seasonal campaigns
- [ ] Update target segments

---

## 🚨 Troubleshooting During Setup

### Issue: "Migration not found"
**Solution:**
```bash
python manage.py migrate core 0088_promotion_backend_models
python manage.py migrate
```

### Issue: "Module not found" (rest_framework)
**Solution:**
```bash
pip install djangorestframework
```

### Issue: 404 on API endpoints
**Solution:** Verify in core/urls.py:
```python
path('promotions/', include('core.promotion_urls')),
```

### Issue: 403 Forbidden on API
**Solution:** Ensure user is logged in and is vendor user

### Issue: Models not showing in admin
**Solution:** Verify core/admin.py has:
```python
from core.promotion_admin import *
```

---

## 📞 Support Resources

### Quick Reference
1. **API Endpoints** → PROMOTION_BACKEND_API_DOCUMENTATION.md
2. **Quick Setup** → PROMOTION_BACKEND_QUICK_START.md
3. **Code Examples** → core/promotion_utils.py
4. **Admin Interface** → core/promotion_admin.py
5. **DRF ViewSets** → core/promotion_api_views.py

### Getting Help
1. Check documentation files
2. Review example code
3. Test in Django shell
4. Use Django admin interface
5. Check server logs

---

## ✅ Sign-Off Checklist

### Implementation Complete When:
- [ ] All 4 models working
- [ ] All 30+ endpoints tested
- [ ] Admin interface functional
- [ ] Utility functions tested
- [ ] Documentation reviewed
- [ ] Frontend connected (Phase 5)
- [ ] Security verified
- [ ] Performance acceptable
- [ ] Ready for production

---

**🎉 Mark completed items as you progress!**

**Current Status:** Ready for Phase 1 Setup
**Next Step:** Install dependencies and run migration
