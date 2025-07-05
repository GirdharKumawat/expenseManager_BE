import os
from .serializers import UserSerializer,LoginSerializer,RegisterUserSerializer
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.models import User
from google.oauth2 import id_token
from google.auth.transport import requests
from .authentication import CookieJWTAuthentication


COOKIE_SECURE=True
@api_view(['GET'])
@authentication_classes([CookieJWTAuthentication])
@permission_classes([IsAuthenticated])
def check_auth(request):
    return Response({"message": f"Authenticated as {request.user.username}"}, status=status.HTTP_200_OK)

@api_view(['POST'])
def userRegister(request):
    serializer = RegisterUserSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        refresh = RefreshToken.for_user(user) 
        response = Response({
            'user': UserSerializer(user).data,
        })
        response.set_cookie(key='access_token', value=str(refresh.access_token), httponly=True, secure=COOKIE_SECURE, samesite="None")
        response.set_cookie(key='refresh_token', value=str(refresh), httponly=True, secure=COOKIE_SECURE, samesite="None")
        return response
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def userLogin(request):
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)
        response = Response({
            'user': UserSerializer(user).data,
        })
        response.set_cookie(key='access_token', value=str(refresh.access_token), httponly=True, secure=COOKIE_SECURE, samesite="None")
        response.set_cookie(key='refresh_token', value=str(refresh), httponly=True, secure=COOKIE_SECURE, samesite="None")
        return response
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@authentication_classes([CookieJWTAuthentication])
@permission_classes([IsAuthenticated])
def userLogout(request):
        response = Response({'msg':'Logout successfully'},status=status.HTTP_205_RESET_CONTENT)
        response.delete_cookie('access_token')
        response.delete_cookie('refresh_token')
        
        return response
    
@api_view(['POST'])
@authentication_classes([CookieJWTAuthentication])
def cookieTokenRefresh(request):  
    refresh_token = request.COOKIES.get("refresh_token")
    print(f"Refresh token from cookies: {refresh_token}")
    if not refresh_token:
        return Response({"error": "No refresh token provided."}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        token = RefreshToken(refresh_token)
        access_token = str(token.access_token)
        response = Response({
            'Msg': 'Token refreshed successfully',
        })
        response.set_cookie(key='access_token', value=access_token, httponly=True, secure=COOKIE_SECURE, samesite="None")
        return response
    except Exception as e:
        return Response({"error": f"Failed to refresh token: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
    

@api_view(['POST'])
def google_login(request):
    token = request.data.get('id_token')
    if not token:
        return Response({'error': 'Token not provided'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        # Verify token with Google's public keys
        idinfo = id_token.verify_oauth2_token(
            token,
            requests.Request(),
            os.getenv('GOOGLE_CLIENT_ID')
        )

        email = idinfo.get('email')
        name = idinfo.get('name', '')
        picture = idinfo.get('picture', '')

        if not email:
            return Response({'error': 'Google account email not found.'}, status=status.HTTP_400_BAD_REQUEST)

        # Use email as unique identifier
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                'username': email.split('@')[0],  # use part before @
                'first_name': name.split(' ')[0],
                'last_name': ' '.join(name.split(' ')[1:]),
            }
        )

        refresh = RefreshToken.for_user(user)

        response = Response({'msg': 'Login successful'}, status=status.HTTP_200_OK)
        response.set_cookie(
            key='access_token',
            value=str(refresh.access_token),
            httponly=True,
            secure=COOKIE_SECURE,
            samesite="None"
        )
        response.set_cookie(
            key='refresh_token',
            value=str(refresh),
            httponly=True,
            secure=COOKIE_SECURE,
            samesite="None"
        )
        return response

    except ValueError as e:
        return Response({'error': 'Invalid Google token'}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        # Optional: log the error
        return Response({'error': 'Internal server error', 'details': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
