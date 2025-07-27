from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django.shortcuts import redirect
from django.db import models
from .serializers import CustomUserSerializer, UserRegistrationSerializer
from .permissions import IsSuperAdminPermission

User = get_user_model()

class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = CustomUserSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        # Return the current user's profile.
        return self.request.user

@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    # Public user registration endpoint. Alternative to Djoser's registration for custom handling.
    serializer = UserRegistrationSerializer(data=request.data)
    
    if serializer.is_valid():
        user = serializer.save()
        
        # Generate JWT tokens for the new user
        refresh = RefreshToken.for_user(user)
        access_token = refresh.access_token
        
        return Response({
            'message': 'User registered successfully',
            'user': CustomUserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(access_token),
            }
        }, status=status.HTTP_201_CREATED)
    
    return Response({
        'error': 'Registration failed',
        'details': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST', 'GET'])
@permission_classes([IsAuthenticated])
def logout_user(request):
    """
    Logout endpoint that blacklists the refresh token.
    Supports both POST (with refresh token) and GET (session logout).
    """
    try:
        if request.method == 'POST':
            # JWT token logout
            refresh_token = request.data.get('refresh_token')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            
            return Response({
                'message': 'Successfully logged out (JWT)'
            }, status=status.HTTP_200_OK)
        
        elif request.method == 'GET':
            # Session logout - redirect to frontend logout
            return redirect('/logout/')
    
    except Exception as e:
        return Response({
            'error': 'Logout failed',
            'details': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_info(request):
    user = request.user
    serializer = CustomUserSerializer(user)
    
    # Add additional role information
    role_permissions = {}
    if user.role:
        role_permissions = user.role.permissions or {}
    else:
        # Use default permissions for users without a role (equivalent to old Guest role)
        role_permissions = user.get_default_permissions()
    
    return Response({
        'user': serializer.data,
        'role_permissions': role_permissions,
        'is_super_admin': user.is_super_admin(),
        'is_admin_or_above': user.is_admin_or_above(),
        'is_teacher_or_above': user.is_teacher_or_above(),
    }, status=status.HTTP_200_OK)


class UserListView(generics.ListAPIView):
    queryset = User.objects.all().select_related('role')
    serializer_class = CustomUserSerializer
    permission_classes = [IsSuperAdminPermission]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by role if provided
        role_name = self.request.query_params.get('role', None)
        if role_name:
            queryset = queryset.filter(role__name=role_name)
        
        # Search by username, email, or name
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                models.Q(username__icontains=search) |
                models.Q(email__icontains=search) |
                models.Q(first_name__icontains=search) |
                models.Q(last_name__icontains=search)
            )
        
        return queryset.order_by('-date_joined')
