from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse
def version(request):
    return HttpResponse("Expense Manager BE API Version 1.34.1")
urlpatterns = [
    # Admin interface
    path('admin/', admin.site.urls),
    path('version/', version, name='version'),
     
    path('', include('base.urls')),
]

