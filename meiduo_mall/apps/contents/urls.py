from django.urls import path

from apps.contents import views

urlpatterns=[
    path('index',views.IndexView.as_view())
]