from django.urls import path

from . import views

urlpatterns = [
    path('reporters/', views.reporters),
    path('issues/', views.issues),
]