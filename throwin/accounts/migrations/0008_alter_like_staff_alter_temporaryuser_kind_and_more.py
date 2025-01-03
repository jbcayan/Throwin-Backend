# Generated by Django 5.1.2 on 2024-11-19 03:43

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0007_alter_user_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='like',
            name='staff',
            field=models.ForeignKey(limit_choices_to={'kind': 'restaurant_staff'}, on_delete=django.db.models.deletion.CASCADE, related_name='likes', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='temporaryuser',
            name='kind',
            field=models.CharField(choices=[('super_admin', 'Super Admin'), ('admin', 'Admin'), ('restaurant_staff', 'Restaurant Staff'), ('consumer', 'Consumer'), ('undefined', 'Undefined')], default='undefined', max_length=50),
        ),
        migrations.AlterField(
            model_name='user',
            name='kind',
            field=models.CharField(choices=[('super_admin', 'Super Admin'), ('admin', 'Admin'), ('restaurant_staff', 'Restaurant Staff'), ('consumer', 'Consumer'), ('undefined', 'Undefined')], default='undefined', max_length=50),
        ),
    ]
