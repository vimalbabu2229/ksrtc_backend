# Generated by Django 5.0.6 on 2024-06-25 17:53

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('depot', '0002_alter_vehicle_reg_no'),
        ('employee', '0002_alter_employee_pen_number_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Schedule',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start_time', models.TimeField()),
                ('end_time', models.TimeField()),
                ('steering_duty', models.TimeField()),
                ('spread_over', models.TimeField()),
            ],
        ),
        migrations.CreateModel(
            name='DutyList',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(default='schedule', max_length=50)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('is_active', models.BooleanField()),
                ('description', models.TextField(null=True)),
                ('depot', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='depot.depot')),
            ],
        ),
        migrations.CreateModel(
            name='DutyListMapper',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('conductor', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='scheduled_conductor', to='employee.employee')),
                ('driver', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='scheduled_driver', to='employee.employee')),
                ('duty_list', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='scheduler.dutylist')),
                ('vehicle', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='depot.vehicle')),
                ('schedule', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='scheduler.schedule')),
            ],
        ),
        migrations.CreateModel(
            name='TripSchedulerMapper',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('index', models.IntegerField()),
                ('terminal_gap', models.TimeField()),
                ('schedule', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='scheduler.schedule')),
                ('trip', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='depot.trip')),
            ],
        ),
    ]