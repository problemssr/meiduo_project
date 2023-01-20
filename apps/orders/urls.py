from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^place/order/$', views.PlaceOrderView.as_view(), name='placeorder'),
    url(r'^orders/commit/$', views.OrderView.as_view(), name='order'),
    url(r'^orders/success/$', views.OrderSuccessView.as_view(), name='sucess'),

]
