from django.urls import path

from apps.verifications import views

urlpatterns = [
    path('images_code/<int:uuid>/', views.ImageCodeView.as_view()),

    # path(r'^login/$', views.LoginView.as_view(), name='login'),
    # path(r'^logout/$', views.LogoutView.as_view(), name='logout'),
    # path(r'^center/$', views.UserCenterInfoView.as_view(), name='center'),
]
