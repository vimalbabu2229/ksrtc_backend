from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet,ViewSet
from rest_framework import status
from rest_framework.permissions import IsAuthenticated 
from .models import Employee, Depot
from .serializers import ProfileSerializer

class EmployeeProfileView(ViewSet):
    permission_classes=[IsAuthenticated]

    def list(self, request):
        user = request.user
        if user.is_active:
            try:
                data = Employee.objects.get(user=user.id)
                serializer = ProfileSerializer(data)
                return Response(serializer.data, status=status.HTTP_200_OK)
            except Employee.DoesNotExist:
                return Response({'error': 'Employee profile does not exist'}, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({'error': 'You are not an active user . Please contact deport admin'}, status=status.HTTP_401_UNAUTHORIZED)
