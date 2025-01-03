# Generated by Django 5.1.2 on 2024-11-19 03:43

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payment_service', '0002_paymenthistory_user_nick_name'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name='disbursementrequest',
            name='staff',
            field=models.ForeignKey(limit_choices_to={'kind': 'restaurant_staff'}, on_delete=django.db.models.deletion.CASCADE, related_name='disbursement_requests', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='paymenthistory',
            name='staff',
            field=models.ForeignKey(limit_choices_to={'kind': 'restaurant_staff'}, on_delete=django.db.models.deletion.CASCADE, related_name='received_payments', to=settings.AUTH_USER_MODEL),
        ),
    ]
