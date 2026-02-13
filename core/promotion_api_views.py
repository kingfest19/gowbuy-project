"""
Django REST Framework ViewSets for promotion management APIs.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum, Avg, Count
from django.shortcuts import get_object_or_404

from core.models import (
    Promotion, PromotionVariant, PromotionSegmentRule,
    PromotionCode, PromotionCampaign, Vendor, Order
)
from core.promotion_serializers import (
    PromotionListSerializer, PromotionDetailSerializer,
    PromotionVariantSerializer, PromotionSegmentRuleSerializer,
    PromotionCodeSerializer, PromotionCampaignSerializer
)


class PromotionViewSet(viewsets.ModelViewSet):
    """ViewSet for promotion CRUD and management"""
    serializer_class = PromotionDetailSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['is_active', 'scope', 'promo_type']
    search_fields = ['name', 'code', 'description']
    ordering_fields = ['created_at', 'start_date', 'usage_count']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Get promotions for current vendor"""
        vendor = get_object_or_404(Vendor, user=self.request.user)
        return Promotion.objects.filter(applicable_vendor=vendor)
    
    def get_serializer_class(self):
        """Use different serializers for list vs detail"""
        if self.action == 'list':
            return PromotionListSerializer
        return PromotionDetailSerializer
    
    @action(detail=True, methods=['get'])
    def analytics(self, request, pk=None):
        """Get analytics for a specific promotion"""
        promotion = self.get_object()
        
        variants = promotion.variants.all()
        
        analytics = {
            'promotion_id': promotion.id,
            'promotion_name': promotion.name,
            'total_variants': variants.count(),
            'total_revenue': float(variants.aggregate(Sum('revenue_generated'))['revenue_generated__sum'] or 0),
            'total_conversions': variants.aggregate(Sum('conversions'))['conversions__sum'] or 0,
            'total_clicks': variants.aggregate(Sum('clicks'))['clicks__sum'] or 0,
            'total_impressions': variants.aggregate(Sum('impressions'))['impressions__sum'] or 0,
            'avg_conversion_rate': round(
                sum([v.conversion_rate for v in variants]) / max(len(variants), 1), 2
            ),
            'codes_generated': promotion.promo_codes.count(),
            'codes_redeemed': promotion.promo_codes.filter(status='redeemed').count(),
        }
        
        return Response(analytics)
    
    @action(detail=True, methods=['get'])
    def performance_by_segment(self, request, pk=None):
        """Get performance breakdown by customer segment"""
        promotion = self.get_object()
        
        segment_performance = []
        for rule in promotion.segment_rules.filter(is_active=True):
            segment_performance.append({
                'segment_type': rule.get_segment_type_display(),
                'description': rule.description if hasattr(rule, 'description') else '',
                'is_active': rule.is_active,
            })
        
        return Response(segment_performance)
    
    @action(detail=True, methods=['post'])
    def duplicate_with_new_dates(self, request, pk=None):
        """Duplicate a promotion with new dates"""
        promotion = self.get_object()
        
        # Create new promotion
        new_promotion = Promotion.objects.create(
            name=f"{promotion.name} (Copy)",
            description=promotion.description,
            promo_type=promotion.promo_type,
            discount_value=promotion.discount_value,
            scope=promotion.scope,
            start_date=request.data.get('start_date'),
            end_date=request.data.get('end_date'),
            minimum_purchase_amount=promotion.minimum_purchase_amount,
            usage_limit=promotion.usage_limit,
            uses_per_customer=promotion.uses_per_customer,
            applicable_vendor=promotion.applicable_vendor,
        )
        
        # Copy relationships
        new_promotion.applicable_categories.set(promotion.applicable_categories.all())
        new_promotion.applicable_products.set(promotion.applicable_products.all())
        
        serializer = self.get_serializer(new_promotion)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class PromotionVariantViewSet(viewsets.ModelViewSet):
    """ViewSet for A/B testing variants"""
    serializer_class = PromotionVariantSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Get variants for vendor's promotions"""
        vendor = get_object_or_404(Vendor, user=self.request.user)
        return PromotionVariant.objects.filter(promotion__applicable_vendor=vendor)
    
    @action(detail=True, methods=['post'])
    def mark_winner(self, request, pk=None):
        """Mark this variant as the winner"""
        variant = self.get_object()
        
        # Mark all variants for this promotion as non-winners
        PromotionVariant.objects.filter(promotion=variant.promotion).update(is_winner=False)
        
        # Mark this as winner
        variant.is_winner = True
        variant.save(update_fields=['is_winner'])
        
        # Update promotion
        variant.promotion.discount_value = variant.discount_value
        variant.promotion.save(update_fields=['discount_value'])
        
        serializer = self.get_serializer(variant)
        return Response({
            'detail': 'Variant marked as winner',
            'variant': serializer.data
        })
    
    @action(detail=True, methods=['post'])
    def record_impression(self, request, pk=None):
        """Record a customer impression for this variant"""
        variant = self.get_object()
        variant.impressions += 1
        variant.save(update_fields=['impressions'])
        return Response({'impressions': variant.impressions})
    
    @action(detail=True, methods=['post'])
    def record_click(self, request, pk=None):
        """Record a click for this variant"""
        variant = self.get_object()
        variant.clicks += 1
        variant.save(update_fields=['clicks'])
        return Response({'clicks': variant.clicks})
    
    @action(detail=True, methods=['post'])
    def record_conversion(self, request, pk=None):
        """Record a conversion for this variant"""
        variant = self.get_object()
        order_id = request.data.get('order_id')
        revenue = request.data.get('revenue', 0)
        
        variant.conversions += 1
        variant.revenue_generated += float(revenue) if revenue else 0
        variant.save(update_fields=['conversions', 'revenue_generated'])
        
        return Response({
            'conversions': variant.conversions,
            'revenue_generated': float(variant.revenue_generated)
        })


class SegmentRuleViewSet(viewsets.ModelViewSet):
    """ViewSet for customer segment rules"""
    serializer_class = PromotionSegmentRuleSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Get segment rules for vendor's promotions"""
        vendor = get_object_or_404(Vendor, user=self.request.user)
        return PromotionSegmentRule.objects.filter(promotion__applicable_vendor=vendor)
    
    @action(detail=False, methods=['post'])
    def check_eligibility(self, request):
        """Check if current user is eligible for a promotion's segments"""
        promotion_id = request.data.get('promotion_id')
        promotion = get_object_or_404(Promotion, id=promotion_id)
        
        segment_rules = promotion.segment_rules.filter(is_active=True)
        
        eligible_segments = []
        for rule in segment_rules:
            if rule.qualifies_customer(request.user):
                eligible_segments.append(rule.get_segment_type_display())
        
        return Response({
            'promotion_id': promotion.id,
            'user_id': request.user.id,
            'eligible_segments': eligible_segments,
            'is_eligible': len(eligible_segments) > 0 or segment_rules.count() == 0
        })


class PromotionCodeViewSet(viewsets.ModelViewSet):
    """ViewSet for promotion codes"""
    serializer_class = PromotionCodeSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['status', 'promotion']
    search_fields = ['code']
    ordering_fields = ['created_at', 'redeemed_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Get codes for vendor's promotions"""
        vendor = get_object_or_404(Vendor, user=self.request.user)
        return PromotionCode.objects.filter(promotion__applicable_vendor=vendor)
    
    @action(detail=True, methods=['post'])
    def redeem(self, request, pk=None):
        """Redeem a promotion code"""
        code = self.get_object()
        
        try:
            # Get order ID from request
            order_id = request.data.get('order_id')
            order = get_object_or_404(Order, id=order_id)
            
            # Redeem the code
            code.redeem(request.user, order)
            
            serializer = self.get_serializer(code)
            return Response({
                'detail': 'Code redeemed successfully',
                'code': serializer.data
            })
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get statistics on code usage"""
        promotion_id = request.query_params.get('promotion_id')
        
        if not promotion_id:
            return Response({'error': 'promotion_id required'}, status=status.HTTP_400_BAD_REQUEST)
        
        codes = self.get_queryset().filter(promotion_id=promotion_id)
        
        stats = {
            'total_codes': codes.count(),
            'active_codes': codes.filter(status='active').count(),
            'redeemed_codes': codes.filter(status='redeemed').count(),
            'disabled_codes': codes.filter(status='disabled').count(),
            'expired_codes': codes.filter(status='expired').count(),
            'redemption_rate': 0,
        }
        
        if stats['total_codes'] > 0:
            stats['redemption_rate'] = round((stats['redeemed_codes'] / stats['total_codes']) * 100, 2)
        
        return Response(stats)
    
    @action(detail=False, methods=['post'])
    def bulk_generate(self, request):
        """Generate bulk promotion codes"""
        promotion_id = request.data.get('promotion_id')
        quantity = int(request.data.get('quantity', 100))
        
        # Limit quantity
        if quantity > 10000:
            return Response({
                'error': 'Maximum 10,000 codes per request'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        promotion = get_object_or_404(Promotion, id=promotion_id)
        
        import secrets
        import string
        
        generated_codes = []
        charset = string.ascii_uppercase + string.digits
        
        for _ in range(quantity):
            while True:
                code = ''.join(secrets.choice(charset) for _ in range(10))
                if not PromotionCode.objects.filter(code=code).exists():
                    break
            
            generated_codes.append(PromotionCode(
                promotion=promotion,
                code=code,
                status='active'
            ))
        
        created = PromotionCode.objects.bulk_create(generated_codes)
        
        return Response({
            'success': True,
            'quantity_created': len(created),
            'message': f'{len(created)} codes generated successfully',
            'codes_sample': [c.code for c in created[:5]]
        }, status=status.HTTP_201_CREATED)


class PromotionCampaignViewSet(viewsets.ModelViewSet):
    """ViewSet for promotion campaigns"""
    serializer_class = PromotionCampaignSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['status']
    search_fields = ['name', 'description']
    ordering_fields = ['created_at', 'start_date']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Get campaigns for current vendor"""
        vendor = get_object_or_404(Vendor, user=self.request.user)
        return PromotionCampaign.objects.filter(vendor=vendor)
    
    def perform_create(self, serializer):
        """Set vendor on create"""
        vendor = get_object_or_404(Vendor, user=self.request.user)
        serializer.save(vendor=vendor)
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate a campaign"""
        campaign = self.get_object()
        campaign.status = 'active'
        campaign.save(update_fields=['status'])
        
        serializer = self.get_serializer(campaign)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def pause(self, request, pk=None):
        """Pause a campaign"""
        campaign = self.get_object()
        campaign.status = 'paused'
        campaign.save(update_fields=['status'])
        
        serializer = self.get_serializer(campaign)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def end(self, request, pk=None):
        """End a campaign"""
        campaign = self.get_object()
        campaign.status = 'ended'
        campaign.save(update_fields=['status'])
        
        serializer = self.get_serializer(campaign)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def performance(self, request, pk=None):
        """Get detailed performance metrics"""
        campaign = self.get_object()
        metrics = campaign.get_performance_metrics()
        
        return Response({
            'campaign_id': campaign.id,
            'campaign_name': campaign.name,
            'metrics': metrics,
            'performance_summary': {
                'status': 'high' if metrics['total_revenue'] > 10000 else 'medium' if metrics['total_revenue'] > 1000 else 'low',
                'roi_estimate': round((metrics['total_revenue'] / max(1, metrics['total_conversions'])), 2) if metrics['total_conversions'] > 0 else 0
            }
        })
    
    @action(detail=True, methods=['get'])
    def promotion_breakdown(self, request, pk=None):
        """Get performance breakdown by promotion"""
        campaign = self.get_object()
        
        breakdown = []
        for promo in campaign.promotions.all():
            variants = promo.variants.all()
            breakdown.append({
                'promotion_id': promo.id,
                'promotion_name': promo.name,
                'promotion_code': promo.code or 'Auto',
                'variant_count': variants.count(),
                'revenue': float(variants.aggregate(Sum('revenue_generated'))['revenue_generated__sum'] or 0),
                'conversions': variants.aggregate(Sum('conversions'))['conversions__sum'] or 0,
                'roi': round(
                    (variants.aggregate(Sum('revenue_generated'))['revenue_generated__sum'] or 0) /
                    max(variants.aggregate(Sum('conversions'))['conversions__sum'] or 1, 1), 2
                )
            })
        
        return Response(breakdown)
