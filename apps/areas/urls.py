from django.conf.urls import url

from apps.areas import views

urlpatterns = [
    url(r'^areas/$', views.AreasView.as_view(), name='areas'),
]
