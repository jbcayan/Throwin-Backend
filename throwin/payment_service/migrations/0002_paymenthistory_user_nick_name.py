# Generated by Django 5.1.2 on 2024-11-13 07:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payment_service', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='paymenthistory',
            name='user_nick_name',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
    ]
