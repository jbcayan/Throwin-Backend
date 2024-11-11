from django.urls import path
from . import views

urlpatterns = [
    path('dummy/', views.dummy_payment_view, name='dummy_payment'),
]
