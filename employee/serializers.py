from rest_framework import serializers
from .models import Employee, LeaveApplication
from depot.models import Depot

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = ['user', 'name', 'pen_number', 'phone_number', 'designation', 'date_of_join', 'on_leave']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['email'] = instance.user.email
        representation['depot'] = Depot.objects.get(user=instance.depot).office
        return representation
    
class LeaveApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveApplication
        exclude = ['employee']

    leave_from = serializers.DateField(
        input_formats=['%d-%m-%Y'],  # Input format
        format='%d-%m-%Y'            # Output format
    )
    leave_till = serializers.DateField(
        input_formats=['%d-%m-%Y'],  # Input format
        format='%d-%m-%Y'            # Output format
    )

class LeaveListSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveApplication
        fields = ['id', 'leave_type', 'leave_from', 'leave_till']