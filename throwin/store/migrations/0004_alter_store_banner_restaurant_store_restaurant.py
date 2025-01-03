# Generated by Django 5.1.2 on 2024-12-28 06:39

import core.utils
import django.db.models.deletion
import uuid
import versatileimagefield.fields
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0003_store_created_by_store_updated_by_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name='store',
            name='banner',
            field=versatileimagefield.fields.VersatileImageField(blank=True, null=True, upload_to=core.utils.get_store_banner_file_prefix, verbose_name='Store Banner'),
        ),
        migrations.CreateModel(
            name='Restaurant',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uid', models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, unique=True)),
                ('status', models.CharField(choices=[('active', 'Active'), ('inactive', 'Inactive'), ('deleted', 'Deleted'), ('pending', 'Pending')], default='active', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=100)),
                ('slug', models.SlugField(blank=True, null=True, unique=True)),
                ('description', models.TextField(blank=True, null=True)),
                ('logo', versatileimagefield.fields.VersatileImageField(blank=True, null=True, upload_to=core.utils.get_restaurant_logo_file_prefix, verbose_name='restaurant logo')),
                ('banner', versatileimagefield.fields.VersatileImageField(blank=True, null=True, upload_to=core.utils.get_restaurant_banner_file_prefix, verbose_name='restaurant banner')),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created_by', to=settings.AUTH_USER_MODEL, verbose_name='Created Person')),
                ('updated_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated_by', to=settings.AUTH_USER_MODEL, verbose_name='Updated Person')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='store',
            name='restaurant',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='stores', to='store.restaurant'),
        ),
    ]
