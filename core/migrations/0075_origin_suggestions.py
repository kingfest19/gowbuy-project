# Generated migration for adding origin suggestion fields and OriginLabel model
from django.db import migrations, models
import django.db.models.deletion
import django_countries.fields
from django.conf import settings

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0074_product_origin_country_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='suggested_origin_country',
            field=django_countries.fields.CountryField(max_length=2, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='product',
            name='origin_confidence',
            field=models.FloatField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='product',
            name='origin_inferred_by',
            field=models.CharField(max_length=20, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='product',
            name='origin_inference_metadata',
            field=models.JSONField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='product',
            name='origin_inferred_at',
            field=models.DateTimeField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='product',
            name='origin_inference_status',
            field=models.CharField(default='none', max_length=20),
        ),
        migrations.CreateModel(
            name='OriginLabel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('label_country', django_countries.fields.CountryField(max_length=2, null=True, blank=True)),
                ('confidence', models.FloatField(null=True, blank=True)),
                ('note', models.TextField(blank=True)),
                ('source', models.CharField(default='admin', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='origin_labels', to='core.product')),
                ('labeler', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ('-created_at',),
            },
        ),
    ]
