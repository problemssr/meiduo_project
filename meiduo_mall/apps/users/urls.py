from django.urls import path

from apps.users import views

urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='register'),
    path('usernames/<str:username>/count/', views.UsernameCountView.as_view(), name='usernamecount'),

    # path(r'^login/$', views.LoginView.as_view(), name='login'),
    # path(r'^logout/$', views.LogoutView.as_view(), name='logout'),
    # path(r'^center/$', views.UserCenterInfoView.as_view(), name='center'),
]
