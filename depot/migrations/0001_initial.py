# Generated by Django 5.0.6 on 2024-06-19 20:32

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('accounts', '0006_remove_employee_depot_remove_employee_user_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Depot',
            fields=[
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, serialize=False, to=settings.AUTH_USER_MODEL)),
                ('office', models.CharField(max_length=50)),
                ('ato', models.CharField(max_length=50)),
                ('district', models.CharField(max_length=50)),
            ],
        ),
    ]
