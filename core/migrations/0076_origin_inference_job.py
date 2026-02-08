# Generated migration for OriginInferenceJob model
from django.db import migrations, models
import django.db.models.deletion
import django_countries.fields

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0075_origin_suggestions'),
    ]

    operations = [
        migrations.CreateModel(
            name='OriginInferenceJob',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('started_at', models.DateTimeField(blank=True, null=True)),
                ('finished_at', models.DateTimeField(blank=True, null=True)),
                ('status', models.CharField(choices=[('PENDING', 'Pending'), ('STARTED', 'Started'), ('SUCCESS', 'Success'), ('FAILED', 'Failed')], default='PENDING', max_length=20)),
                ('params', models.JSONField(blank=True, null=True)),
                ('summary', models.JSONField(blank=True, null=True)),
                ('error', models.TextField(blank=True, null=True)),
            ],
            options={
                'ordering': ('-created_at',),
                'verbose_name': 'Origin Inference Job',
                'verbose_name_plural': 'Origin Inference Jobs',
            },
        ),
    ]
