from rest_framework import serializers
from .models import Depot, Vehicle, Trip
from  employee.models import Employee 

class DepotSerializer(serializers.ModelSerializer):
    class Meta:
        model = Depot
        fields = ['office', 'ato', 'district']

class EmployeeUserSerializer(serializers.Serializer):
    email = serializers.EmailField()
    date_of_join = serializers.DateField() # YYYY-MM-DD

class EmployeeProfileSerializer(serializers.ModelSerializer):
    class Meta :
        model = Employee
        fields = '__all__'

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
        fields = ['id',
                  'departure_place', 
                  'departure_time', 
                  'arrival_place', 
                  'arrival_time', 
                  'route', 
                  'km', 
                  'running_time',
                  'status',
                  ]