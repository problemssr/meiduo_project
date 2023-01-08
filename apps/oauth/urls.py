from django.conf.urls import url
from . import views
urlpatterns = [
    url(r'^qq/login/$',views.OauthQQURLView.as_view(),name='qqlogin'),
    url(r'^oauth_callback/$',views.OauthQQUserView.as_view(),name='oauthcallback'),
]