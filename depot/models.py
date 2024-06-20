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