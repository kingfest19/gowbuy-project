"""
Django REST Framework serializers for promotion models.
"""
from rest_framework import serializers
from core.models import (
    Promotion, PromotionVariant, PromotionSegmentRule,
    PromotionCode, PromotionCampaign
)


class PromotionVariantSerializer(serializers.ModelSerializer):
    """Serializer for A/B Testing promotion variants"""
    ctr = serializers.SerializerMethodField()
    conversion_rate = serializers.SerializerMethodField()
    avg_order_value = serializers.SerializerMethodField()
    
    class Meta:
        model = PromotionVariant
        fields = [
            'id', 'promotion', 'variant_type', 'discount_value',
            'description', 'impressions', 'clicks', 'conversions',
            'revenue_generated', 'is_winner', 'ctr', 'conversion_rate',
            'avg_order_value', 'created_at'
        ]
        read_only_fields = ['id', 'impressions', 'clicks', 'conversions', 'revenue_generated', 'created_at']
    
    def get_ctr(self, obj):
        """Click-through rate"""
        return round(obj.ctr, 2)
    
    def get_conversion_rate(self, obj):
        """Conversion rate"""
        return round(obj.conversion_rate, 2)
    
    def get_avg_order_value(self, obj):
        """Average order value"""
        return round(float(obj.avg_order_value), 2)


class PromotionSegmentRuleSerializer(serializers.ModelSerializer):
    """Serializer for customer segmentation rules"""
    segment_type_display = serializers.CharField(source='get_segment_type_display', read_only=True)
    
    class Meta:
        model = PromotionSegmentRule
        fields = [
            'id', 'promotion', 'segment_type', 'segment_type_display',
            'min_total_spent', 'min_orders_count', 'days_since_last_order',
            'country_codes', 'is_active', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class PromotionCodeSerializer(serializers.ModelSerializer):
    """Serializer for promotion codes"""
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    redeemed_by_username = serializers.CharField(source='redeemed_by.username', read_only=True, allow_null=True)
    
    class Meta:
        model = PromotionCode
        fields = [
            'id', 'code', 'promotion', 'status', 'status_display',
            'redeemed_by', 'redeemed_by_username', 'redeemed_at',
            'redeemed_order', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'redeemed_at', 'created_at', 'updated_at']


class PromotionCampaignSerializer(serializers.ModelSerializer):
    """Serializer for promotion campaigns"""
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    promotion_count = serializers.SerializerMethodField()
    is_active_now = serializers.SerializerMethodField()
    performance_metrics = serializers.SerializerMethodField()
    promotions_list = serializers.SerializerMethodField()
    
    class Meta:
        model = PromotionCampaign
        fields = [
            'id', 'vendor', 'name', 'description', 'promotions',
            'promotions_list', 'start_date', 'end_date', 'status',
            'status_display', 'emoji', 'impressions', 'clicks',
            'revenue_generated', 'promotion_count', 'is_active_now',
            'performance_metrics', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'impressions', 'clicks', 'revenue_generated',
            'created_at', 'updated_at'
        ]
    
    def get_promotion_count(self, obj):
        """Count of promotions in campaign"""
        return obj.promotion_count
    
    def get_is_active_now(self, obj):
        """Check if campaign is currently active"""
        return obj.is_active_now
    
    def get_performance_metrics(self, obj):
        """Get performance metrics"""
        metrics = obj.get_performance_metrics()
        return {
            'total_impressions': metrics['total_impressions'],
            'total_clicks': metrics['total_clicks'],
            'total_conversions': metrics['total_conversions'],
            'total_revenue': float(metrics['total_revenue']),
            'conversion_rate': round(metrics['conversion_rate'], 2),
        }
    
    def get_promotions_list(self, obj):
        """Get list of promotion names"""
        return list(obj.promotions.values_list('name', flat=True))


class PromotionListSerializer(serializers.ModelSerializer):
    """Serializer for listing promotions with variant count"""
    variant_count = serializers.SerializerMethodField()
    active_variant_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Promotion
        fields = [
            'id', 'name', 'code', 'promo_type', 'discount_value',
            'scope', 'start_date', 'end_date', 'usage_limit',
            'usage_count', 'is_active', 'variant_count',
            'active_variant_count', 'created_at'
        ]
        read_only_fields = ['id', 'usage_count', 'created_at']
    
    def get_variant_count(self, obj):
        """Count of A/B variants"""
        return obj.variants.count()
    
    def get_active_variant_count(self, obj):
        """Count of active variants"""
        return obj.variants.filter(is_winner=False).count()


class PromotionDetailSerializer(serializers.ModelSerializer):
    """Detailed promotion serializer with variants and segments"""
    variants = PromotionVariantSerializer(many=True, read_only=True)
    segment_rules = PromotionSegmentRuleSerializer(many=True, read_only=True)
    codes_count = serializers.SerializerMethodField()
    codes_redeemed = serializers.SerializerMethodField()
    
    class Meta:
        model = Promotion
        fields = [
            'id', 'name', 'description', 'code', 'promo_type',
            'discount_value', 'scope', 'applicable_categories',
            'applicable_products', 'applicable_vendor', 'start_date',
            'end_date', 'minimum_purchase_amount', 'usage_limit',
            'usage_count', 'uses_per_customer', 'is_active',
            'variants', 'segment_rules', 'codes_count', 'codes_redeemed',
            'created_at'
        ]
        read_only_fields = ['id', 'usage_count', 'created_at']
    
    def get_codes_count(self, obj):
        """Total promotion codes generated"""
        return obj.promo_codes.count()
    
    def get_codes_redeemed(self, obj):
        """Number of codes redeemed"""
        return obj.promo_codes.filter(status='redeemed').count()
