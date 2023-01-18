"""meiduo_mall URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.contrib import admin

from django.http import HttpResponse


def log(request):
    """
    1.日志的作用是为了方便我们的项目部署上线之后分析问题
    2.日志的配置 我们直接复制到setting中就可以了
    3.日志的级别     DEBUG,info,warning,error,CRITICAL
    4.使用
        import logging

        logger = logging.getLogger(setting_name)

        logger.info()
        logger.warnging()
        logger.error()

    :param request:
    :return:
    """
    # 1.导入
    import logging
    # 2.创建日志器
    logger = logging.getLogger('django')
    # 3.记录
    logger.info('info~~~~')
    logger.warning('warnging')

    return HttpResponse('log')


urlpatterns = [
    # url(r'^log/',log),
    url(r'^admin/', admin.site.urls),

    url(r'^', include(('apps.users.urls', 'users'), namespace='users')),
    url(r'^', include(('apps.contents.urls', 'contents'), namespace='contents')),
    url(r'^', include(('apps.verifications.urls', 'verifications'), namespace='verifications')),
    url(r'^', include(('apps.oauth.urls', 'oauth'), namespace='oauth')),
    url(r'^', include(('apps.areas.urls', 'areas'), namespace='areas')),
    url(r'^', include(('apps.goods.urls', 'goods'), namespace='goods')),
    url(r'^', include(('apps.carts.urls', 'carts'), namespace='carts')),
    # url(r'^',include(('apps.orders.urls', 'orders'),namespace='orders')),
    # url(r'^',include(('apps.pay.urls', 'pay'),namespace='pay')),

    url(r'^search/', include('haystack.urls')),
]
