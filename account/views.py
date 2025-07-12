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
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator


COOKIE_SECURE=True  # Required when using SameSite=None
SAME_SITE='None'  # For cross-origin requests
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
        response.set_cookie(key='access_token', value=str(refresh.access_token), httponly=True, secure=COOKIE_SECURE, samesite=SAME_SITE)
        response.set_cookie(key='refresh_token', value=str(refresh), httponly=True, secure=COOKIE_SECURE, samesite=SAME_SITE)
        return response
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def userLogin(request):
    serializer = LoginSerializer(data=request.data)
    print("Login attempt with data:", request.data)
    print("---------------------------------------- ")
    if serializer.is_valid():
        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)
        response = Response({
            'user': UserSerializer(user).data,
        })
        response.set_cookie(key='access_token', value=str(refresh.access_token), httponly=True, secure=COOKIE_SECURE, samesite=SAME_SITE)
        response.set_cookie(key='refresh_token', value=str(refresh), httponly=True, secure=COOKIE_SECURE, samesite=SAME_SITE)
        return response
    print("Serializer errors:", serializer.errors)
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
        response.set_cookie(key='access_token', value=access_token, httponly=True, secure=COOKIE_SECURE, samesite=SAME_SITE)
        return response
    except Exception as e:
        return Response({"error": f"Failed to refresh token: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
    

@api_view(['POST', 'OPTIONS'])
@csrf_exempt
def google_login(request):
    origin = request.headers.get('Origin') or 'https://expensemanager.girdharkumawat.site'

    # Preflight request
    if request.method == 'OPTIONS':
        response = Response({'status': 'OK'})
    else:
        # Main POST logic
        token = request.data.get('id_token')
        print(f"[Google Login] Received token: {token[:50] + '...'}" if token else "[Google Login] No token provided")
        print(f"[Google Login] Request headers: {dict(request.headers)}")

        if not token:
            response = Response({'error': 'Token not provided'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            try:
                google_client_id = os.getenv('GOOGLE_CLIENT_ID')
                if not google_client_id:
                    return Response({'error': 'Google OAuth not configured'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

                idinfo = id_token.verify_oauth2_token(token, requests.Request(), google_client_id)
                print(f"[Google Login] Token verified for email: {idinfo.get('email')}")

                email = idinfo.get('email')
                name = idinfo.get('name', '')
                picture = idinfo.get('picture', '')

                if not email:
                    return Response({'error': 'Google account email not found.'}, status=status.HTTP_400_BAD_REQUEST)

                # Create or get user
                user, created = User.objects.get_or_create(
                    email=email,
                    defaults={
                        'username': email.split('@')[0],
                        'first_name': name.split(' ')[0] if name else '',
                        'last_name': ' '.join(name.split(' ')[1:]) if name else '',
                    }
                )

                print(f"[Google Login] User {'created' if created else 'found'}: {user.email}")

                # Generate JWT tokens
                refresh = RefreshToken.for_user(user)

                response = Response({
                    'message': 'Login successful',
                    'user': {
                        'id': user.id,
                        'email': user.email,
                        'username': user.username,
                        'first_name': user.first_name,
                        'last_name': user.last_name,
                    }
                }, status=status.HTTP_200_OK)

                # Set cookies
                COOKIE_SECURE = True
                SAME_SITE = 'None'

                response.set_cookie(
                    key='access_token',
                    value=str(refresh.access_token),
                    httponly=True,
                    secure=COOKIE_SECURE,
                    samesite=SAME_SITE,
                    max_age=60 * 60 * 24  # 1 day
                )
                response.set_cookie(
                    key='refresh_token',
                    value=str(refresh),
                    httponly=True,
                    secure=COOKIE_SECURE,
                    samesite=SAME_SITE,
                    max_age=60 * 60 * 24 * 7  # 7 days
                )

            except ValueError as e:
                print(f"[Google Login] Token verification failed: {str(e)}")
                response = Response({'error': 'Invalid Google token', 'details': str(e)}, status=status.HTTP_400_BAD_REQUEST)

            except Exception as e:
                print(f"[Google Login] Internal error: {str(e)}")
                response = Response({'error': 'Internal server error', 'details': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # ✅ Always set these headers on ALL responses
    response['Access-Control-Allow-Origin'] = origin
    response['Access-Control-Allow-Credentials'] = 'true'
    response['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
    response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'

    return response