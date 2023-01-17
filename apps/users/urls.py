from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^register/$', views.RegisterView.as_view(), name='register'),

    url(r'^usernames/(?P<username>[a-zA-Z0-9_]{5,20})/count/', views.UsernameCountView.as_view(), name='usernamecount'),

    url(r'^login/$', views.LoginView.as_view(), name='login'),
    url(r'^logout/$', views.LogoutView.as_view(), name='logout'),
    url(r'^center/$', views.UserCenterInfoView.as_view(), name='center'),
    url(r'^emails/$', views.EmailView.as_view(), name='email'),
    url(r'^email_active/$', views.EmailActiveView.as_view(), name='activeemail'),
    url(r'^addresses/$', views.AddressView.as_view(), name='showaddress'),
    url(r'^addresses/(?P<address_id>\d+)/$', views.AddressUpdateView.as_view(), name='updateaddress'),
    url(r'^addresses/(?P<address_id>\d+)/default/$', views.DefaultAddressView.as_view(), name='defaultaddress'),
    url(r'^addresses/(?P<address_id>\d+)/title/$', views.UpdateTitleAddressView.as_view(), name='tiitleaddress'),

]
