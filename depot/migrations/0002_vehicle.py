# Generated by Django 5.0.6 on 2024-06-21 14:32

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('depot', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Vehicle',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reg_no', models.CharField(max_length=50)),
                ('type', models.CharField(choices=[('f', 'Fuel'), ('e', 'Electric')], max_length=5)),
                ('year', models.CharField(max_length=10)),
                ('is_active', models.BooleanField(default=True)),
                ('is_available', models.BooleanField(default=True)),
                ('depot', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='depot.depot')),
            ],
        ),
    ]