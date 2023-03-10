import re

from django import http
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views import View

from apps.users.models import User
import logging

logger = logging.getLogger('django')


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
            # return http.HttpResponseBadRequest('数据库异常')

        # 4.返回响应, 跳转到首页

        # 注册完成之后,默认认为用户已经登陆了
        # 保持登陆的状态
        # session
        # 自己实现request.session

        # 系统也能自己去帮助我们实现 登陆状态的保持
        from django.contrib.auth import login
        login(request, user)

        return redirect(reverse('index'))
        # return http.HttpResponse('注册成功')


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
        # 5.验证用户名和密码
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

            # 合并cookie数据到redis中
            merge_cookie_to_redis(request, user, response)

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
