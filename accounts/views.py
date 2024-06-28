from django.contrib.auth import authenticate
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated
from .models import User
from .serializers import LoginSerializer,ChangePasswordSerializer


class AuthViewSet(viewsets.ViewSet):

    # Login 
    @action(detail=False, methods=['post'])
    def login(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            password = serializer.validated_data['password']
            user = authenticate(username=email, password=password)
            if user is not None:
                token, created = Token.objects.get_or_create(user=user)
                return Response({'token':token.key}, status=status.HTTP_200_OK)
            else :
                return Response({'error': 'Invalid Credentials'}, status=status.HTTP_401_UNAUTHORIZED)
        else :
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # Logout
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])    
    def logout(self, request):
        try:
            request.user.auth_token.delete()
            return Response({'message':'Successfully logged out'}, status=status.HTTP_200_OK)
        except :
            return Response({'error':'Invalid credentials '}, status=status.HTTP_400_BAD_REQUEST)
    
    # Reset Password
    @action(detail=False, methods=['patch'], permission_classes=[IsAuthenticated])
    def reset_password(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        # Verify the old password is valid 
        if serializer.is_valid():
            user = request.user
            old_password = serializer.validated_data['old_password']
            new_password = serializer.validated_data['new_password']
            if user.check_password(old_password):
                user.set_password(new_password)
                user.save()
                return Response({'message':'Password changed successfully'}, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'Old password is invalid'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)