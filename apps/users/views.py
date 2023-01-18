import json
import re

from django import http
from django.contrib.auth import login
from django.shortcuts import render, redirect

# Create your views here.
from django.urls import reverse
from django.views import View
from django_redis import get_redis_connection

from apps.goods.models import SKU
from apps.users.models import User, Address
import logging

from apps.users.utils import active_email_url, check_email_active_token
from meiduo_mall import settings
from utils.response_code import RETCODE

logger = logging.getLogger('django')
"""
断点的优势:
    1.可以查看我们的方法是否被调用了
    2.可以查看程序在运行过程中的数据
    3.查看程序的执行顺序是否和预期的一致

断点如何添加:
    0.不要在属性,类上加断点
    1.在函数(方法)的入口处
    2.在需要验证的地方添加
"""


class RegisterView(View):
    """
    1.用户名我们需要判断是否重复(这个要开发一个视图)
            用户名的长度有5-20个的要求
    2.密码 有长度的限制 8-20 要求为 字母,数字,_
    3.确认密码 和密码一致
    4.手机号   手机号得先满足规则
        再判断手机号是否重复
    5.图片验证码是一个后端功能
        图片验证码是为了防止 计算机攻击我们发送短信的功能
    6.短信发送
    7.必须同意协议
    8.注册也是一个功能


    必须要和后端交互的是:
        1.用户名/手机号是否重复
        2.图片验证码
        3.短信
        4.注册功能
    """

    def get(self, request):

        return render(request, 'register.html')

    def post(self, request):
        """
        1.接收前端提交的用户名,密码和手机号
        2.数据的验证(我们不相信前端提交的任何数据)
            2.1 验证比传(必须要让前端传递给后端)的数据是否有值
            2.2 判断用户名是否符合规则
            2.3 判断密码是否 符合规则
            2.4 判断确认密码和密码是否一致
            2.5 判断手机号是否符合规则
        3.验证数据没有问题才入库
        4.返回响应
        """
        # 1.接收前端提交的用户名,密码和手机号
        data = request.POST
        username = data.get('username')
        passwrod = data.get('password')
        passwrod2 = data.get('password2')
        mobile = data.get('mobile')
        # 2.数据的验证(我们不相信前端提交的任何数据)
        #     2.1 验证必传(必须要让前端传递给后端)的数据是否有值
        # all([el,el,el]) el必须有值 只要有一个为None 则为False
        if not all([username, passwrod, passwrod2, mobile]):
            return http.HttpResponseBadRequest('参数有问题')
        #     2.2 判断用户名是否符合规则 判断 5-20位 数字 字母 _
        if not re.match(r'[0-9a-zA-Z_]{5,20}', username):
            return http.HttpResponseBadRequest('用户名不合法')
        #     2.3 判断密码是否 符合规则
        if not re.match(r'[0-9a-zA-Z_]{8,20}', passwrod):
            return http.HttpResponseBadRequest('密码不合法')
        #     2.4 判断确认密码和密码是否一致
        if passwrod != passwrod2:
            return http.HttpResponseBadRequest('密码不一致')
        #     2.5 判断手机号是否符合规则
        if not re.match(r'1[3-9]\d{9}', mobile):
            return http.HttpResponseBadRequest('手机号不符合规则')
        # 2.6 验证同意协议是否勾选

        # 3.验证数据没有问题才入库
        # 当我们在操作外界资源(mysql,redis,file)的时候,我们最好进行 try except的异常处理
        # User.objects.create  直接入库 理论是没问题的 但是 大家会发现 密码是明文
        try:
            user = User.objects.create_user(username=username, password=passwrod, mobile=mobile)
        except Exception as e:
            logger.error(e)
            return render(request, 'register.html', context={'error_message': '数据库异常'})
            return http.HttpResponseBadRequest('数据库异常')

        # 4.返回响应, 跳转到首页

        # 注册完成之后,默认认为用户已经登陆了
        # 保持登陆的状态
        # session
        # 自己实现request.session

        # 系统也能自己去帮助我们实现 登陆状态的保持
        from django.contrib.auth import login
        login(request, user)

        return redirect(reverse('contents:index'))
        # return http.HttpResponse('注册成功')


"""
一 把需求写下来 (前端需要收集什么 后端需要做什么)

二 把大体思路写下来(后端的大体思路)

三 把详细思路完善一下(纯后端)

四 确定我们请求方式和路由


一 把需求写下来 (前端需要收集什么 后端需要做什么)
    当用户把用户名写完成之后,前端应该收集用户名信息, 传递给后端
    后端需要验证 用户名是否重复
二 把大体思路写下来(后端的大体思路)
        前端: 失去焦点之后,发送一个ajax 请求 这个请求包含 用户名
        后端:  接收数据 , 查询用户名
三 把详细思路完善一下
        1. 接收用户名
        2. 查询数据库,通过查询记录的count来判断是否重复 0表示没有重复 1表示重复
四 确定我们请求方式和路由
        敏感数据 推荐使用POST

        GET     usernames/?username=xxxx

        GET     usernames/xxxx/count/  v
"""


class UsernameCountView(View):

    def get(self, request, username):
        # 1. 接收用户名

        # 2. 查询数据库,通过查询记录的count来判断是否重复 0表示没有重复 1表示重复
        try:
            count = User.objects.filter(username=username).count()
        except Exception as e:
            logger.error(e)
            return http.JsonResponse({'code': 400, 'errmsg': '数据库异常'})
        # 3.返回相应
        return http.JsonResponse({'code': 0, 'count': count})


# class Person(object):
#     pass
#
# Person()

"""

一 把需求写下来 (前端需要收集什么 后端需要做什么)
    当用户把用户名/手机号 和密码填写完成之后, 发送给后端
    后端 验证 用户名和密码
二 把大体思路写下来(后端的大体思路)

    1.后端需要接收数据
    2.验证数据
    3.如果验证成功则登陆
      如果验证不成功则失败

三 把详细思路完善一下(纯后端)

    1.后端需要接收数据 (username,password)
    2.判断参数是否齐全
    3.判断用户名是否符合规则
    4.判断密码是否符合规则
    5.验证用户名和密码
    6.如果验证成功则登陆,状态保持
    7.如果验证不成功则提示 用户名或密码错误

四 确定我们请求方式和路由

    POST    login/
"""


class LoginView(View):

    def get(self, request):

        return render(request, 'login.html')

    def post(self, request):
        # 1.后端需要接收数据 (username,password)
        username = request.POST.get('username')
        passwrod = request.POST.get('password')
        remembered = request.POST.get('remembered')
        # 2.判断参数是否齐全
        if not all([username, passwrod]):
            return http.HttpResponseBadRequest('缺少必须的参数')
        # 3.判断用户名是否符合规则
        if not re.match(r'^[a-zA-Z0-9_-]{5,20}$', username):
            return http.HttpResponseBadRequest('用户名不符合规则')
        # 4.判断密码是否符合规则
        if not re.match(r'', passwrod):
            return http.HttpResponseBadRequest('密码不符合规则')
        # 5.验证用户名和密码re
        # 验证有2种方式
        # ① 使用django的认证后端
        # ② 我们可以自己查询数据库( 根据用户名/手机号查询对应的user用户,再比对密码)

        from django.contrib.auth import authenticate
        # 默认的认证后端是调用了 from django.contrib.auth.backends import ModelBackend
        # ModelBackend 中的认证方法
        # def authenticate(self, request, username=None, password=None, **kwargs):

        # 如果用户名和密码正确,则返回user
        # 否则返回None
        user = authenticate(username=username, password=passwrod)

        # is_authenticated 是否是认证用户
        # 登陆用户返回 true
        # 未登陆用户返回 false
        # request.user.is_authenticated

        if user is not None:
            # 6.如果验证成功则登陆,状态保持
            # 登陆成功
            login(request, user)
            if remembered == 'on':
                # 记住登陆
                # request.session.set_expiry(seconds)
                request.session.set_expiry(30 * 24 * 3600)
            else:
                # 不记住
                request.session.set_expiry(0)

            # 如果有next参数,则跳转到指定页面
            # 如果没有next参数,则跳转到首页
            next = request.GET.get('next')
            if next:
                response = redirect(next)
            else:

                response = redirect(reverse('contents:index'))

            # 设置cookie
            # response.set_cookie(key,value,max_age)
            response.set_cookie('username', user.username, max_age=14 * 24 * 3600)

            return response
        else:
            # 登陆失败
            # 7.如果验证不成功则提示 用户名或密码错误
            return render(request, 'login.html', context={'account_errmsg': '用户名或密码错误'})


"""
1.需求
    用户点击退出,就把登陆的信息删除

2. 执行request.session.flush()


"""


class LogoutView(View):

    def get(self, request):
        # request.session.flush()

        # 系统其他也给我们提供了退出的方法
        from django.contrib.auth import logout

        logout(request)

        # 退出之后,我们要跳转到指定页面
        # 还跳转到首页
        # 需要额外删除cookie中的name,因为我们首页的用户信息展示是通过username来判断

        response = redirect(reverse('contents:index'))

        response.delete_cookie('username')

        return response


"""
用户中心 必须是登陆用户才可以访问

当前的问题是: 我们没有登陆也显示了
"""
from django.contrib.auth.mixins import LoginRequiredMixin


class UserCenterInfoView(LoginRequiredMixin, View):

    def get(self, request):
        # request.user 就是登陆的用户的信息

        context = {
            'username': request.user.username,
            'email': request.user.email,
            'mobile': request.user.mobile,
            'email_active': request.user.email_active
        }

        return render(request, 'user_center_info.html', context=context)


"""
一 把需求写下来 (前端需要收集什么 后端需要做什么)
    当用户把邮箱内容填写完成之后,点击保存按钮. 前端需要收集用户的邮箱信息,然后发送一个ajax请求

    后端 要接收数据,然后保存数据,再发送激活邮件


    ,用户一点击就可以激活
二 把大体思路写下来(后端的大体思路)
        1.接收数据
        2.验证数据
        3.保存数据
        4.发送激活邮件
        5.返回相应
三 把详细思路完善一下(纯后端)

        1.接收数据,获取数据
        2.验证数据
        3.保存数据(更新指定用户的邮箱信息)
        4.发送激活邮件
            4.1 激活邮件的内容
            4.2 能够发送激活邮件
        5.返回相应

四 确定我们请求方式和路由

        GET     :一般是获取数据
        POST    :一般是注册(新增)数据

        PUT     :一般是修改数据  (提交的数据在请求body中)    emails/
        DELETE  :一般是删除数据


"""


# class EmailView(LoginRequiredJSONMixin, View):
class EmailView(View):

    def put(self, request):
        # 1.接收数据,获取数据
        data = json.loads(request.body.decode())
        email = data.get('email')
        # 2.验证数据
        if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return http.JsonResponse({'code': RETCODE.PARAMERR, 'errmsg': '参数错误'})
        # 3.保存数据(更新指定用户的邮箱信息)
        try:
            request.user.email = email
            request.user.save()
        except Exception as e:
            return http.JsonResponse({'code': RETCODE.DBERR, 'errmsg': '数据保存失败'})
        # # 发送激活邮件
        # subject = '主题'
        # message = "内容"
        # from_email = settings.EMAIL_FROM
        # html_message = '<h1>哈哈哈哈和</h1>'
        # recipient_list = ['2298269347@qq.com']
        # from django.core.mail import send_mail
        # send_mail(
        #     subject=subject,
        #     message=message,
        #     from_email=from_email,
        #     recipient_list=recipient_list,
        #     html_message=html_message
        # )
        # '2298269347@qq.com'
        #
        verify_url = active_email_url(email, request.user.id)

        from celery_tasks.email.tasks import send_active_email
        send_active_email.delay(email, verify_url)
        #     4.1 激活邮件的内容
        #     4.2 能够发送激活邮件
        # 5.返回相应
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'ok'})


class EmailActiveView(View):
    def get(self, request):
        # 1.获取token
        token = request.GET.get('token')
        if token is None:
            return http.HttpResponseBadRequest('缺少参数')
        # 2.解密token数据
        # 3.根据解密的数据查询用户信息
        user = check_email_active_token(token)
        if user is None:
            return http.HttpResponseBadRequest('没有此用户')
        # 4.修改用户信息
        user.email_active = True
        user.save()
        # 5.跳转到个人中心页面
        return redirect(reverse('users:center'))


class AddressView(LoginRequiredMixin, View):
    """用户收货地址"""

    def post(self, request):
        # 一个人最多添加20个地址
        # 0 先判断当前的用户的地址是否多余等于20个
        # 获取当前用户的地址的数量
        # count = Address.objects.filter(user=request.user).count()
        # count = request.user.address_set.count()
        count = request.user.addresses.all().count()

        if count >= 5:
            return http.JsonResponse({'code': RETCODE.THROTTLINGERR, 'errmsg': '地址超过上限'})

        # 1.接收数据 -- 收件人,地址,省,市,区,邮箱,固定电话,手机号
        json_dict = json.loads(request.body.decode())
        receiver = json_dict.get('receiver')
        province_id = json_dict.get('province_id')
        city_id = json_dict.get('city_id')
        district_id = json_dict.get('district_id')
        place = json_dict.get('place')
        mobile = json_dict.get('mobile')
        tel = json_dict.get('tel')
        email = json_dict.get('email')
        # 2.验证数据
        #         验证邮箱,固定电话,手机号 等
        if not all([receiver, province_id, city_id, district_id, place, mobile]):
            return http.HttpResponseBadRequest('缺少必传参数')
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return http.HttpResponseBadRequest('参数mobile有误')
        if tel:
            if not re.match(r'^(0[0-9]{2,3}-)?([2-9][0-9]{6,7})+(-[0-9]{1,4})?$', tel):
                return http.HttpResponseBadRequest('参数tel有误')
        if email:
            if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
                return http.HttpResponseBadRequest('参数email有误')
        # 3.数据入库
        try:
            # address = Address()
            # address.save()

            address = Address.objects.create(
                user=request.user,
                title=receiver,
                receiver=receiver,
                province_id=province_id,
                city_id=city_id,
                district_id=district_id,
                place=place,
                mobile=mobile,
                tel=tel,
                email=email
            )
        except Exception as e:
            logger.error(e)

        # 如果当前用户没有默认地址就给它设置一个默认地址
        if not request.user.default_address:
            request.user.default_address = address
            request.user.save()

        address_dict = {
            "id": address.id,
            "title": address.title,
            "receiver": address.receiver,
            "province": address.province.name,
            "city": address.city.name,
            "district": address.district.name,
            "place": address.place,
            "mobile": address.mobile,
            "tel": address.tel,
            "email": address.email
        }
        # 4.返回相应
        #     返回JSON数据
        return http.JsonResponse({"code": RETCODE.OK, 'errmsg': 'ok', 'address': address_dict})

    def get(self, request):
        """提供收货地址界面"""
        # 1.根据条件查询信息
        addresses = Address.objects.filter(user=request.user, is_deleted=False)

        # 2.如果需要我们将对象列表转换为字典列表
        addresses_list = []
        for address in addresses:
            addresses_list.append({
                "id": address.id,
                "title": address.title,
                "receiver": address.receiver,
                "province": address.province.name,
                "province_id": address.province_id,
                "city": address.city.name,
                "city_id": address.city_id,
                "district": address.district.name,
                "district_id": address.district_id,
                "place": address.place,
                "mobile": address.mobile,
                "tel": address.tel,
                "email": address.email
            })
        # 3.返回相应
        context = {
            'addresses': addresses_list,
            'default_address_id': request.user.default_address_id
        }
        return render(request, 'user_center_site.html', context)


class AddressUpdateView(View):
    def put(self, request, address_id):
        # 1.接收前端提交的修改数据
        json_dict = json.loads(request.body.decode())
        receiver = json_dict.get('receiver')
        province_id = json_dict.get('province_id')
        city_id = json_dict.get('city_id')
        district_id = json_dict.get('district_id')
        place = json_dict.get('place')
        mobile = json_dict.get('mobile')
        tel = json_dict.get('tel')
        email = json_dict.get('email')

        # 校验参数
        if not all([receiver, province_id, city_id, district_id, place, mobile]):
            return http.HttpResponseBadRequest('缺少必传参数')
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return http.HttpResponseBadRequest('参数mobile有误')
        if tel:
            if not re.match(r'^(0[0-9]{2,3}-)?([2-9][0-9]{6,7})+(-[0-9]{1,4})?$', tel):
                return http.HttpResponseBadRequest('参数tel有误')
        if email:
            if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
                return http.HttpResponseBadRequest('参数email有误')

        #     3.获取修改哪条数据(id)
        #    4.根据id查询数据
        # address = Address.objects.get(id=address_id)
        # #    5.更新(修改)数据
        # address.receiver=receiver
        # address.mobile=mobile
        # address.save()

        try:
            Address.objects.filter(id=address_id).update(
                user=request.user,
                title=receiver,
                receiver=receiver,
                province_id=province_id,
                city_id=city_id,
                district_id=district_id,
                place=place,
                mobile=mobile,
                tel=tel,
                email=email
            )
        except Exception as e:
            logger.error(e)
            return http.JsonResponse({'code': RETCODE.DBERR, 'errmsg': '数据更新失败'})

        #    6.返回相应
        address = Address.objects.get(id=address_id)
        address_dict = {
            "id": address.id,
            "title": address.title,
            "receiver": address.receiver,
            "province": address.province.name,
            "city": address.city.name,
            "district": address.district.name,
            "place": address.place,
            "mobile": address.mobile,
            "tel": address.tel,
            "email": address.email
        }

        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'ok', 'address': address_dict})

    def delete(self, request, address_id):
        # 1.获取删除哪条数据(id)
        # 2.查询数据库
        try:
            address = Address.objects.get(id=address_id)
        except Address.DoesNotExist:
            return http.JsonResponse({'code': RETCODE.NODATAERR, 'errmsg': '暂无此数据'})
        # 3.删除数据
        # address.delete() 物理删除
        try:
            address.is_deleted = True  # 逻辑删除
            address.save()
        except Exception as e:
            logger.error(e)
            return http.JsonResponse({'code': RETCODE.DBERR, 'errmsg': '删除失败'})
        # 4.返回相应
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'ok'})


class DefaultAddressView(View):
    def put(self, request, address_id):
        """设置默认地址"""
        try:
            # 接收参数,查询地址
            address = Address.objects.get(id=address_id)

            # 设置地址为默认地址
            request.user.default_address = address
            request.user.save()
        except Exception as e:
            logger.error(e)
            return http.JsonResponse({'code': RETCODE.DBERR, 'errmsg': '设置默认地址失败'})

        # 响应设置默认地址结果
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': '设置默认地址成功'})


class UpdateTitleAddressView(View):
    """设置地址标题"""

    def put(self, request, address_id):
        """设置地址标题"""
        # 接收参数：地址标题
        json_dict = json.loads(request.body.decode())
        title = json_dict.get('title')

        try:
            # 查询地址
            address = Address.objects.get(id=address_id)

            # 设置新的地址标题
            address.title = title
            address.save()
        except Exception as e:
            logger.error(e)
            return http.JsonResponse({'code': RETCODE.DBERR, 'errmsg': '设置地址标题失败'})

        # 4.响应删除地址结果
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': '设置地址标题成功'})


"""
用户浏览记录的需求:
    1.我们只记录登陆用户的浏览记录
    2.当用户浏览某一个具体的商品的时候,我们需要将该记录添加到一个表中
        一 把需求写下来 (前端需要收集什么 后端需要做什么)

            前端就是收集 商品id和用户信息,而且是发送ajax 请求

            后端就是要保存数据

        二 把大体思路写下来(后端的大体思路)

           接收数据
           验证数据
           保存数据
           返回相应

        三 把详细思路完善一下(纯后端)

           1.接收数据  用户信息,商品id
           2.验证数据
           3.保存数据(后台:mysql /redis中)
            保存在列表中
            3.1 连接redis
            3.2  先删除有可能存在的这个商品id
            3.3  再添加商品id
            3.4  因为最近浏览没有分页功能我们只保存5条历史记录
           4.返回相应


        四 确定我们请求方式和路由
            POST    user_histroy/


    3.获取用户浏览记录的时候需要有一个展示顺序

        根据用户id,获取redis中的指定数据
        [1,2,34,] 根据id查询商品详细信息
        [SKu,SKU,SKU] 对象转换为字典
        返回相应


        GET     histories/

"""


class AddUserHistroyView(View):
    def get(self, request):
        # 根据用户id,获取redis中的指定数据
        user = request.user

        redis_conn = get_redis_connection('history')
        # [1,2,34,] 根据id查询商品详细信息
        ids = redis_conn.lrange('history_%s' % user.id, 0, 4)
        # [SKu,SKU,SKU] 对象转换为字典
        sku_list = []
        for id in ids:
            sku = SKU.objects.get(pk=id)
            sku_list.append({
                'id': sku.id,
                'name': sku.name,
                'default_image_url': sku.default_image.url,
                'price': sku.price
            })

        # 返回相应
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'ok', 'skus': sku_list})

    def post(self, request):
        # 1.接收数据  用户信息,商品id
        user = request.user

        data = json.loads(request.body.decode())
        sku_id = data.get('sku_id')
        # 2.验证数据
        try:
            # pk primary key 主键 当前的主键就是 id
            SKU.objects.get(pk=sku_id)
            # SKU.objects.get(id=sku_id)
        except SKU.DoesNotExist:
            return http.JsonResponse({'codd': RETCODE.NODATAERR, 'errmsg': '暂无次商品'})
        # 3.保存数据(后台:mysql /redis中)
        #  保存在列表中
        #  3.1 连接redis
        redis_conn = get_redis_connection('history')
        #  3.2  先删除有可能存在的这个商品id
        # http://doc.redisfans.com/
        # LREM key count value
        redis_conn.lrem('history_%s' % user.id, 0, sku_id)
        #  3.3  再添加商品id
        redis_conn.lpush('history_%s' % user.id, sku_id)
        #  3.4  因为最近浏览没有分页功能我们只保存5条历史记录
        redis_conn.ltrim('history_%s' % user.id, 0, 4)
        # 4.返回相应
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'ok'})
