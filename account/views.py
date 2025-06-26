from .serializers import UserSerializer, LoginSerializer, RegisterUserSerializer
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .authentication import CookieJWTAuthentication
 


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
        response.set_cookie(key='access_token', value=str(refresh.access_token), httponly=True, secure=False,samesite="None")
        response.set_cookie(key='refresh_token', value=str(refresh), httponly=True, secure=False,samesite="None")
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
        response.set_cookie(key='access_token', value=str(refresh.access_token), httponly=True, secure=False, samesite="lax")
        response.set_cookie(key='refresh_token', value=str(refresh), httponly=True, secure=False, samesite="lax")
        return response
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@authentication_classes([CookieJWTAuthentication])
@permission_classes([IsAuthenticated])
def userLogout(request):
    print("User logout called")
    response = Response({"message": "Logout successful"}, status=status.HTTP_200_OK)
    response.delete_cookie('access_token')
    response.delete_cookie('refresh_token')
    
    return response
    
@api_view(['POST'])
def cookieTokenRefresh(request):  
    refresh_token = request.COOKIES.get("refresh_token")
    if not refresh_token:
        return Response({"error": "No refresh token provided."}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        token = RefreshToken(refresh_token)
        access_token = str(token.access_token)
        response = Response({
            'Msg': 'Token refreshed successfully',
        })
        response.set_cookie(key='access_token', value=access_token, httponly=True, secure=False, samesite="lax")
        return response
    except Exception as e:
        return Response({"error": f"Failed to refresh token: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
    
