"""
Django Admin configuration for promotion backend models.
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Sum, Avg
from core.models import (
    PromotionVariant, PromotionSegmentRule,
    PromotionCode, PromotionCampaign
)


@admin.register(PromotionVariant)
class PromotionVariantAdmin(admin.ModelAdmin):
    """Admin for A/B Testing promotion variants"""
    list_display = [
        'id', 'promotion', 'variant_type', 'discount_value',
        'impressions_display', 'conversions_display', 'revenue_display',
        'conversion_rate_display', 'is_winner_display'
    ]
    list_filter = ['variant_type', 'is_winner', 'promotion__promo_type', 'created_at']
    search_fields = ['promotion__name', 'promotion__code', 'description']
    readonly_fields = [
        'impressions', 'clicks', 'conversions', 'revenue_generated',
        'created_at', 'ctr_display', 'conversion_rate_display',
        'avg_order_value_display', 'promotion'
    ]
    fieldsets = (
        ('Basic Info', {
            'fields': ('promotion', 'variant_type', 'discount_value', 'description')
        }),
        ('Performance Metrics', {
            'fields': (
                'impressions', 'clicks', 'conversions', 'revenue_generated',
                'ctr_display', 'conversion_rate_display', 'avg_order_value_display'
            ),
            'classes': ('collapse',)
        }),
        ('Winner Selection', {
            'fields': ('is_winner',)
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def impressions_display(self, obj):
        return format_html(f'<strong>{obj.impressions}</strong>')
    impressions_display.short_description = 'Impressions'
    
    def conversions_display(self, obj):
        return format_html(f'<strong>{obj.conversions}</strong>')
    conversions_display.short_description = 'Conversions'
    
    def revenue_display(self, obj):
        return format_html(f'<span style="color: green;"><strong>GH₵ {obj.revenue_generated:.2f}</strong></span>')
    revenue_display.short_description = 'Revenue'
    
    def conversion_rate_display(self, obj):
        rate = obj.conversion_rate
        color = 'green' if rate > 5 else 'orange' if rate > 2 else 'red'
        return format_html(f'<span style="color: {color};">{rate:.2f}%</span>')
    conversion_rate_display.short_description = 'Conv. Rate'
    
    def ctr_display(self, obj):
        return format_html(f'{obj.ctr:.2f}%')
    ctr_display.short_description = 'CTR'
    
    def avg_order_value_display(self, obj):
        return format_html(f'GH₵ {obj.avg_order_value:.2f}')
    avg_order_value_display.short_description = 'Avg Order Value'
    
    def is_winner_display(self, obj):
        if obj.is_winner:
            return format_html('<span style="color: gold;">★ Winner</span>')
        return '—'
    is_winner_display.short_description = 'Status'


@admin.register(PromotionSegmentRule)
class PromotionSegmentRuleAdmin(admin.ModelAdmin):
    """Admin for customer segmentation rules"""
    list_display = ['id', 'promotion', 'segment_type', 'is_active', 'created_at']
    list_filter = ['segment_type', 'is_active', 'created_at']
    search_fields = ['promotion__name', 'promotion__code']
    readonly_fields = ['created_at', 'promotion']
    fieldsets = (
        ('Segment Rule', {
            'fields': ('promotion', 'segment_type', 'is_active')
        }),
        ('Conditions', {
            'fields': (
                'min_total_spent', 'min_orders_count',
                'days_since_last_order', 'country_codes'
            ),
            'description': 'Define conditions for this segment'
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        """Make promotion read-only after creation"""
        if obj:  # Editing an existing object
            return self.readonly_fields + ['segment_type']
        return self.readonly_fields


@admin.register(PromotionCode)
class PromotionCodeAdmin(admin.ModelAdmin):
    """Admin for promotion codes (bulk code generation)"""
    list_display = [
        'code', 'promotion', 'status_display',
        'redeemed_by', 'redeemed_at',
        'created_at'
    ]
    list_filter = ['status', 'promotion', 'created_at', 'redeemed_at']
    search_fields = ['code', 'promotion__name', 'redeemed_by__username']
    readonly_fields = [
        'code', 'promotion', 'redeemed_by', 'redeemed_at',
        'redeemed_order', 'created_at', 'updated_at'
    ]
    fieldsets = (
        ('Code Info', {
            'fields': ('code', 'promotion', 'status')
        }),
        ('Redemption', {
            'fields': ('redeemed_by', 'redeemed_at', 'redeemed_order'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    actions = ['mark_as_redeemed', 'mark_as_disabled', 'disable_codes']
    
    def status_display(self, obj):
        colors = {
            'active': 'blue',
            'redeemed': 'green',
            'expired': 'gray',
            'disabled': 'red',
        }
        color = colors.get(obj.status, 'black')
        return format_html(
            f'<span style="background-color: {color}; color: white; '
            f'padding: 3px 8px; border-radius: 3px;">{obj.get_status_display()}</span>'
        )
    status_display.short_description = 'Status'
    
    def mark_as_redeemed(self, request, queryset):
        updated = queryset.filter(status='active').update(status='redeemed')
        self.message_user(request, f'{updated} codes marked as redeemed')
    mark_as_redeemed.short_description = 'Mark selected as redeemed'
    
    def mark_as_disabled(self, request, queryset):
        updated = queryset.filter(status='active').update(status='disabled')
        self.message_user(request, f'{updated} codes disabled')
    mark_as_disabled.short_description = 'Disable selected codes'
    
    def disable_codes(self, request, queryset):
        updated = queryset.update(status='disabled')
        self.message_user(request, f'{updated} codes disabled')
    disable_codes.short_description = 'Disable codes'


@admin.register(PromotionCampaign)
class PromotionCampaignAdmin(admin.ModelAdmin):
    """Admin for promotion campaigns"""
    list_display = [
        'get_campaign_name', 'vendor', 'status_display',
        'promotion_count_display', 'performance_display',
        'date_range_display', 'is_active_now_display'
    ]
    list_filter = ['status', 'vendor', 'start_date', 'created_at']
    search_fields = ['name', 'description', 'vendor__name']
    filter_horizontal = ['promotions']
    readonly_fields = [
        'impressions', 'clicks', 'revenue_generated',
        'created_at', 'updated_at', 'performance_summary'
    ]
    fieldsets = (
        ('Campaign Info', {
            'fields': ('vendor', 'name', 'description', 'emoji', 'status')
        }),
        ('Promotions', {
            'fields': ('promotions',)
        }),
        ('Schedule', {
            'fields': ('start_date', 'end_date'),
        }),
        ('Performance', {
            'fields': (
                'impressions', 'clicks', 'revenue_generated',
                'performance_summary'
            ),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_campaign_name(self, obj):
        return format_html(f'{obj.emoji} {obj.name}')
    get_campaign_name.short_description = 'Campaign'
    
    def status_display(self, obj):
        colors = {
            'draft': 'gray',
            'scheduled': 'blue',
            'active': 'green',
            'paused': 'orange',
            'ended': 'red',
        }
        color = colors.get(obj.status, 'black')
        return format_html(
            f'<span style="background-color: {color}; color: white; '
            f'padding: 3px 8px; border-radius: 3px;">{obj.get_status_display()}</span>'
        )
    status_display.short_description = 'Status'
    
    def promotion_count_display(self, obj):
        return format_html(f'<strong>{obj.promotion_count}</strong> promotions')
    promotion_count_display.short_description = 'Promotions'
    
    def performance_display(self, obj):
        revenue = obj.revenue_generated or 0
        color = 'green' if revenue > 5000 else 'orange' if revenue > 1000 else 'gray'
        return format_html(
            f'<span style="color: {color}; font-weight: bold;">GH₵ {revenue:.2f}</span>'
        )
    performance_display.short_description = 'Revenue'
    
    def date_range_display(self, obj):
        return f"{obj.start_date.date()} → {obj.end_date.date()}"
    date_range_display.short_description = 'Date Range'
    
    def is_active_now_display(self, obj):
        if obj.is_active_now:
            return format_html('<span style="color: green; font-weight: bold;">✓ Active Now</span>')
        return '—'
    is_active_now_display.short_description = 'Currently Active'
    
    def performance_summary(self, obj):
        """Summary of campaign performance"""
        metrics = obj.get_performance_metrics()
        return format_html(
            '<table style="width: 100%; border-collapse: collapse;">'
            '<tr><td><strong>Total Revenue:</strong></td><td>GH₵ {:.2f}</td></tr>'
            '<tr><td><strong>Conversions:</strong></td><td>{}</td></tr>'
            '<tr><td><strong>Conversion Rate:</strong></td><td>{:.2f}%</td></tr>'
            '</table>',
            metrics['total_revenue'],
            metrics['total_conversions'],
            metrics['conversion_rate']
        )
    performance_summary.short_description = 'Performance Metrics'


# Inline admin for campaign promotions
class PromotionInlineAdmin(admin.TabularInline):
    """Inline admin to see promotions in a campaign"""
    model = PromotionCampaign.promotions.through
    extra = 0
    can_delete = True
