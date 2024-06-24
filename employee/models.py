from django.db import models
from accounts.models import User
from depot.models import Depot
from django.core.validators import MinLengthValidator

#________________________EMPLOYEE MODEL____________________________
class Employee(models.Model):
    EMPLOYEE_TYPE = [
        ('d', 'Driver'),
        ('c', 'Conductor')
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    name = models.CharField(max_length=50)
    pen_number = models.CharField(max_length=50, unique=True)
    phone_number = models.CharField(max_length=10, validators=[MinLengthValidator(10)], unique=True)
    designation = models.CharField(choices=EMPLOYEE_TYPE, max_length=2)
    date_of_join = models.DateField()
    on_leave = models.BooleanField(default=False)
    depot = models.ForeignKey(Depot, on_delete=models.SET_NULL, null=True)

    def __str__(self) -> str:
        return self.name