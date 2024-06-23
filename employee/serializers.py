from rest_framework import serializers
from .models import Employee
from depot.models import Depot

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = ['name', 'pen_number', 'phone_number', 'designation', 'date_of_join', 'on_leave']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['depot'] = Depot.objects.get(user=instance.depot).office
        return representation