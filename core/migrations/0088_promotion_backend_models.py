# Generated migration for promotion backend models
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0087_product_is_deleted'),  # Update this to match your latest migration
    ]

    operations = [
        # PromotionVariant model (A/B Testing)
        migrations.CreateModel(
            name='PromotionVariant',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('variant_type', models.CharField(choices=[('A', 'Variant A (Control)'), ('B', 'Variant B (Test)'), ('C', 'Variant C (Test 2)')], help_text='Variant designation', max_length=1)),
                ('discount_value', models.DecimalField(decimal_places=2, help_text='Different discount value for this variant', max_digits=10)),
                ('description', models.CharField(blank=True, help_text="e.g., 'Premium pricing', 'Standard pricing'", max_length=255)),
                ('impressions', models.PositiveIntegerField(default=0, help_text='How many customers saw this variant')),
                ('clicks', models.PositiveIntegerField(default=0, help_text='How many clicked/used this variant')),
                ('conversions', models.PositiveIntegerField(default=0, help_text='How many converted with this variant')),
                ('revenue_generated', models.DecimalField(decimal_places=2, default=0, help_text='Total revenue from this variant', max_digits=12)),
                ('is_winner', models.BooleanField(default=False, help_text='Mark as winning variant')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('promotion', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='variants', to='core.promotion')),
            ],
            options={
                'verbose_name': 'Promotion Variant',
                'verbose_name_plural': 'Promotion Variants',
                'ordering': ('variant_type',),
                'unique_together': {('promotion', 'variant_type')},
            },
        ),

        # PromotionSegmentRule model
        migrations.CreateModel(
            name='PromotionSegmentRule',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('segment_type', models.CharField(
                    choices=[
                        ('new_customers', 'New Customers Only'),
                        ('loyalty_members', 'Loyalty Program Members'),
                        ('abandoned_cart', 'Abandoned Cart Recovery'),
                        ('high_value', 'High Value Customers'),
                        ('geographic', 'Geographic (Location-based)'),
                        ('first_time', 'First Time Buyers'),
                    ],
                    max_length=20
                )),
                ('min_total_spent', models.DecimalField(blank=True, decimal_places=2, help_text='Min lifetime spending to qualify (for high-value segments)', max_digits=10, null=True)),
                ('min_orders_count', models.PositiveIntegerField(blank=True, help_text='Min number of orders to qualify', null=True)),
                ('days_since_last_order', models.PositiveIntegerField(blank=True, help_text='Days since last order (for re-engagement)', null=True)),
                ('country_codes', models.CharField(blank=True, help_text="Comma-separated country codes (e.g., 'GH,NG,KE')", max_length=255)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('promotion', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='segment_rules', to='core.promotion')),
            ],
            options={
                'verbose_name': 'Promotion Segment Rule',
                'verbose_name_plural': 'Promotion Segment Rules',
                'unique_together': {('promotion', 'segment_type')},
            },
        ),

        # PromotionCode model (Bulk Code Generation)
        migrations.CreateModel(
            name='PromotionCode',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(db_index=True, max_length=50, unique=True)),
                ('status', models.CharField(choices=[('active', 'Active'), ('redeemed', 'Redeemed'), ('expired', 'Expired'), ('disabled', 'Disabled')], default='active', max_length=20)),
                ('redeemed_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('promotion', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='promo_codes', to='core.promotion')),
                ('redeemed_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='redeemed_codes', to=settings.AUTH_USER_MODEL)),
                ('redeemed_order', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='used_promo_codes', to='core.order')),
            ],
            options={
                'verbose_name': 'Promotion Code',
                'verbose_name_plural': 'Promotion Codes',
                'ordering': ('-created_at',),
            },
        ),

        # Add indexes for PromotionCode
        migrations.AddIndex(
            model_name='promotioncode',
            index=models.Index(fields=['promotion', 'status'], name='core_promot_promot_idx'),
        ),
        migrations.AddIndex(
            model_name='promotioncode',
            index=models.Index(fields=['code'], name='core_promot_code_idx'),
        ),

        # PromotionCampaign model
        migrations.CreateModel(
            name='PromotionCampaign',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text="Campaign name (e.g., 'Summer Mega Sale')", max_length=255)),
                ('description', models.TextField(blank=True, help_text='Campaign description and objectives')),
                ('start_date', models.DateTimeField()),
                ('end_date', models.DateTimeField()),
                ('status', models.CharField(choices=[('draft', 'Draft'), ('scheduled', 'Scheduled'), ('active', 'Active'), ('paused', 'Paused'), ('ended', 'Ended')], default='draft', max_length=20)),
                ('emoji', models.CharField(default='🎉', help_text='Emoji for campaign (e.g., ☀️, 🎃, 🎄)', max_length=10)),
                ('impressions', models.PositiveIntegerField(default=0, editable=False)),
                ('clicks', models.PositiveIntegerField(default=0, editable=False)),
                ('revenue_generated', models.DecimalField(decimal_places=2, default=0, editable=False, help_text='Total revenue from campaign', max_digits=12)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('promotions', models.ManyToManyField(help_text='Promotions included in this campaign', related_name='campaigns', to='core.promotion')),
                ('vendor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='promo_campaigns', to='core.vendor')),
            ],
            options={
                'verbose_name': 'Promotion Campaign',
                'verbose_name_plural': 'Promotion Campaigns',
                'ordering': ('-start_date',),
            },
        ),

        # Add indexes for PromotionCampaign
        migrations.AddIndex(
            model_name='promotioncampaign',
            index=models.Index(fields=['vendor', 'status'], name='core_promot_vendor_status_idx'),
        ),
        migrations.AddIndex(
            model_name='promotioncampaign',
            index=models.Index(fields=['start_date', 'end_date'], name='core_promot_date_range_idx'),
        ),
    ]
