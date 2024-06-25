from django.db import models
from depot.models import Trip, Depot, Vehicle
from employee.models import Employee

class Schedule(models.Model):
    start_time = models.TimeField()
    end_time = models.TimeField()
    steering_duty = models.TimeField()
    spread_over = models.TimeField()

class TripSchedulerMapper(models.Model):
    index = models.IntegerField()
    terminal_gap = models.TimeField()
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE)
    schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE)

class DutyList(models.Model):
    name = models.CharField(max_length=50, default="schedule")
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField()
    description = models.TextField(null=True)
    depot = models.ForeignKey(Depot, on_delete=models.SET_NULL, null=True)

class DutyListMapper(models.Model):
    driver = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, related_name='scheduled_driver')
    conductor = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, related_name='scheduled_conductor')
    vehicle = models.ForeignKey(Vehicle, on_delete=models.SET_NULL, null=True)
    schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE)
    duty_list = models.ForeignKey(DutyList, on_delete=models.CASCADE) 
