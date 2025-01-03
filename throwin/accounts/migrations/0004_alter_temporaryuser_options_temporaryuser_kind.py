# Generated by Django 5.1.2 on 2024-10-30 10:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_temporaryuser'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='temporaryuser',
            options={'ordering': ['-created_at']},
        ),
        migrations.AddField(
            model_name='temporaryuser',
            name='kind',
            field=models.CharField(choices=[('super_admin', 'Super Admin'), ('admin', 'Admin'), ('restaurant_stuff', 'Restaurant Stuff'), ('consumer', 'Consumer'), ('undefined', 'Undefined')], default='undefined', max_length=50),
        ),
    ]
