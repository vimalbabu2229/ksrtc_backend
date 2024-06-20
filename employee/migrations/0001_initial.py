# Generated by Django 5.0.6 on 2024-06-19 20:32

import django.db.models.deletion
import phonenumber_field.modelfields
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('accounts', '0006_remove_employee_depot_remove_employee_user_and_more'),
        ('depot', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Employee',
            fields=[
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, serialize=False, to=settings.AUTH_USER_MODEL)),
                ('name', models.CharField(max_length=50)),
                ('pen_number', models.CharField(max_length=50)),
                ('phone_number', phonenumber_field.modelfields.PhoneNumberField(blank=True, max_length=128, region='IN', unique=True)),
                ('designation', models.CharField(choices=[('d', 'Driver'), ('c', 'Conductor')], max_length=2)),
                ('date_of_join', models.DateField()),
                ('on_leave', models.BooleanField(default=False)),
                ('depot', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='depot.depot')),
            ],
        ),
    ]