#子应用路由
from django.conf.urls import url
from apps.carts import views

urlpatterns = [
    url(r'^carts/$',views.CartView.as_view(),name='carts'),
]