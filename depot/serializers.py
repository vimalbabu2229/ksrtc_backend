import os
from rest_framework import serializers
from django.core.exceptions import ValidationError
from .models import Depot, Vehicle, Trip
from  employee.models import Employee 
from accounts.models import User

class DepotSerializer(serializers.ModelSerializer):
    class Meta:
        model = Depot
        fields = ['office', 'ato', 'district']

class EmployeeUserSerializer(serializers.Serializer):
    email = serializers.EmailField()
    date_of_join = serializers.DateField(
        input_formats=['%d-%m-%Y'],  # Input format
        format='%d-%m-%Y'            # Output format
    )

class UserExistValidatorSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['email']

class EmployeeProfileSerializer(serializers.ModelSerializer):
    date_of_join = serializers.DateField(
        input_formats=['%d-%m-%Y'],  # Input format
        format='%d-%m-%Y'            # Output format
    )
    class Meta :
        model = Employee
        fields = [
            'name',
            'pen_number',
            'phone_number',
            'designation',
            'date_of_join', 
            'on_leave'
        ]
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['email'] = instance.user.email
        return representation

class VehicleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehicle
        fields = ['reg_no', 'type', 'year', 'depot']

class GetVehicleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehicle
        fields = ['id', 'reg_no', 'type', 'year', 'is_available']

class TripSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trip
        fields = [
            'id',
            'departure_place', 
            'departure_time', 
            'arrival_place', 
            'arrival_time', 
            'route', 
            'km', 
            'running_time',
            'status',
            ]
        
# CUSTOM FILE FIELD 
class CustomFileField(serializers.FileField):
    def __init__(self, allowed_types=[], **kwargs):
        self.allowed_types = allowed_types
        super().__init__(**kwargs)
    
    def to_internal_value(self, data):
        file_obj = super().to_internal_value(data)

        # validate type 
        file_ext = os.path.splitext(file_obj.name)[1].lower()
        if self.allowed_types and file_ext not in self.allowed_types:
            raise ValidationError(f"File type {file_ext} is not allowed. Allowed types are {', '.join(self.allowed_types)}.")
        
        return file_obj

class DataSetSerializer(serializers.Serializer):
    dataset = CustomFileField(allowed_types=['.xlsx'])