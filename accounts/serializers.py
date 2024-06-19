from rest_framework import serializers 
from .models import Depot
from django.contrib.auth.models import User

class DepotSerializer(serializers.ModelSerializer):
    class Meta:
        model = Depot
        fields = "__all__"


class DepotAuthentication(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'password']