"""
URL patterns for promotion management, A/B testing, campaigns, and analytics.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from core.promotion_api_views import (
    PromotionViewSet, PromotionVariantViewSet,
    SegmentRuleViewSet, PromotionCodeViewSet,
    PromotionCampaignViewSet
)
from core.promotion_views import (
    # Campaign views
    promotion_campaigns_list,
    create_promotion_campaign,
    update_campaign_status,
    campaign_performance,
    # Variant views
    create_promotion_variant,
    get_variant_analytics,
    mark_winning_variant,
    # Segment views
    get_segment_eligibility,
    create_segment_rule,
    list_segment_analytics,
    # Code generation
    generate_bulk_codes,
    export_bulk_codes,
    get_codes_statistics,
    # Analytics
    promotion_analytics_dashboard,
    get_promotion_trend_data,
    get_smart_recommendations,
)

# Initialize router for REST API endpoints
router = DefaultRouter()
router.register(r'promotions', PromotionViewSet, basename='promotion')
router.register(r'variants', PromotionVariantViewSet, basename='variant')
router.register(r'segments', SegmentRuleViewSet, basename='segment')
router.register(r'codes', PromotionCodeViewSet, basename='code')
router.register(r'campaigns', PromotionCampaignViewSet, basename='campaign')

app_name = 'promotions'

urlpatterns = [
    # REST API endpoints
    path('api/', include(router.urls)),
    
    # Campaign management views
    path('campaigns/', promotion_campaigns_list, name='campaigns_list'),
    path('campaigns/create/', create_promotion_campaign, name='campaign_create'),
    path('campaigns/<int:campaign_id>/status/', update_campaign_status, name='campaign_update_status'),
    path('campaigns/<int:campaign_id>/performance/', campaign_performance, name='campaign_performance'),
    
    # A/B Testing / Variants
    path('promotions/<int:promotion_id>/variants/create/', create_promotion_variant, name='variant_create'),
    path('promotions/<int:promotion_id>/variants/analytics/', get_variant_analytics, name='variant_analytics'),
    path('variants/<int:variant_id>/mark-winner/', mark_winning_variant, name='variant_mark_winner'),
    
    # Customer Segmentation
    path('promotions/<int:promotion_id>/eligibility/', get_segment_eligibility, name='segment_eligibility'),
    path('promotions/<int:promotion_id>/segments/create/', create_segment_rule, name='segment_create'),
    path('promotions/<int:promotion_id>/segments/analytics/', list_segment_analytics, name='segment_analytics'),
    
    # Bulk Code Generation
    path('promotions/<int:promotion_id>/codes/generate/', generate_bulk_codes, name='codes_generate'),
    path('promotions/<int:promotion_id>/codes/export/', export_bulk_codes, name='codes_export'),
    path('promotions/<int:promotion_id>/codes/statistics/', get_codes_statistics, name='codes_statistics'),
    
    # Analytics & Dashboard
    path('analytics/', promotion_analytics_dashboard, name='analytics_dashboard'),
    path('analytics/trends/', get_promotion_trend_data, name='analytics_trends'),
    path('promotions/<int:promotion_id>/trends/', get_promotion_trend_data, name='promotion_trends'),
    path('recommendations/', get_smart_recommendations, name='recommendations'),
]
