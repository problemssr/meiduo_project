from django.conf.urls import url
from django.urls import path

from apps.verifications import views

urlpatterns = [
    # path('images_code/<uuid:uuid>/', views.ImageCodeView.as_view()),
    url(r'^image_codes/(?P<uuid>[\w-]+)/$', views.ImageCodeView.as_view()),

]
