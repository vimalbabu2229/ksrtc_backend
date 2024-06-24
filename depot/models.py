from django.db import models
from accounts.models import User

#________________________DEPOT MODEL____________________________
class Depot(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    office = models.CharField(max_length=50)
    ato = models.CharField(max_length=50)
    district = models.CharField(max_length=50)

    def __str__(self) -> str:
        return self.office
    
#____________________________ VEHICLE MODEL _______________________

class Vehicle(models.Model):
    VEHICLE_TYPE = [
        ('f', 'Fuel'),
        ('e', 'Electric')
    ]
    reg_no = models.CharField(max_length=50, unique=True)
    type = models.CharField(choices=VEHICLE_TYPE, max_length=5)
    year = models.CharField(max_length=10)
    is_active = models.BooleanField(default=True)
    is_available = models.BooleanField(default=True)
    depot = models.ForeignKey(Depot, on_delete=models.SET_NULL, null=True)

    def __str__(self) -> str:
        return self.reg_no
    
#____________________________ TRIP MODEL _______________________
class Trip(models.Model):
    departure_place = models.CharField(max_length=50)
    departure_time = models.TimeField()
    arrival_place = models.CharField(max_length=50)
    arrival_time = models.TimeField()
    route = models.CharField(max_length=100)
    km = models.CharField(max_length=10)
    running_time = models.TimeField()
    # is_active is used to check whether the trip is currently active or a deleted trip 
    is_active = models.BooleanField(default=True)
    # status is used to make a trip temporarily inactive to generate specific duty list 
    status = models.BooleanField(default=True)
    depot = models.ForeignKey(Depot, on_delete=models.SET_NULL, null=True)

    def __str__(self) -> str:
        return f"{self.departure_place} - {self.arrival_place}"