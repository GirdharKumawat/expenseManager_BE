from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.decorators import api_view
import os

BaseUrl = os.getenv('BASE_URL')
@api_view(['GET'])
def getRoutes(request):
    Routes = {
        'Token': BaseUrl+'api/auth/token/',
        'Token Refresh': BaseUrl+'api/auth/token/refresh/',
        'User Ragister': BaseUrl+'api/auth/user/ragister/',
        'User Login': BaseUrl+'api/auth/user/login/',
   }
    return Response(Routes)
        