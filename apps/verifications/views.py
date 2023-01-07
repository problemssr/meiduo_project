from django import http
from django.shortcuts import render

# Create your views here.
from django.views import View

from apps.verifications.constants import IMAGE_CODE_EXPIRE_TIME, SMS_CODE_EXPIRE_TIME
from libs.yuntongxun.sms import CCP
from utils.response_code import RETCODE

"""
一 把需求写下来 (前端需要收集什么 后端需要做什么)
    前端需要生成一个随机码(uuid), 把这个随机码给后端

    后端需要生成图片验证码,把这个图片验证码的内容保存到redis中 redis的数据是
    uuid: xxxx  有有效期

二 把大体思路写下来(后端的大体思路)

    1.生成图片验证码和获取图片验证码的内容
    2.连接redis,将 图片验证码保存起来 uuid:xxxx 有有效期
    3.返回图片验证码

三 把详细思路完善一下(纯后端)

    1.生成图片验证码和获取图片验证码的内容
    2.1连接redis,
    2.2将 图片验证码保存起来 uuid:xxxx 有有效期
    3.返回图片验证码

四 确定我们请求方式和路由
    GET     image_codes/(?P<uuid>[\w-]+)/

    GET     image_codes/?uuid=xxxxx


"""
from libs.captcha.captcha import captcha
from django_redis import get_redis_connection
class ImageCodeView(View):

    def get(self,request,uuid):

        # uuid=request.GET.get('uuid')

        # 1.生成图片验证码和获取图片验证码的内容
        text,image = captcha.generate_captcha()
        # 2.1连接redis
        redis_conn = get_redis_connection('code')
        # 2.2将 图片验证码保存起来 uuid:xxxx 有有效期
        # redis_conn.setex(key,senconds,value)
        # redis_conn.setex(uuid,120,text)
        # 我们加了一个前缀
        # redis_conn.setex('img_%s'%uuid,120,text)
        # 增加了代码的可读性
        redis_conn.setex('img_%s'%uuid,IMAGE_CODE_EXPIRE_TIME,text)
        # 3.返回图片验证码
        # content_type  MIME 类型
        # 大类/小类
        # return http.HttpResponse(image)
        # 告知浏览器 这是个图片
        return http.HttpResponse(image,content_type='image/jpeg')


"""
云通讯:
    第一步:
        正式接入步骤：
                注册 》 提交认证 》 充值 》 提交短信模板（免费测试仅需注册）
        测试:
            注册 》免费测试仅需注册


    第二步:
        看文档开发

        1.下载SDK (SDK 可以理解为 django-redis 直接把库(包)安装直接使用 )
        2.修改指定的配置

    第三步：
        验证

用户点击获取短信验证码按钮,我们能够给用户发送短信

一 把需求写下来 (前端需要收集什么 后端需要做什么)
    前端需要收集: 手机号,用户输入的 图片验证码内容 和 UUID
    通过ajax发送给后端
二 把大体思路写下来(后端的大体思路)

    接收参数
    验证参数
    发送短信

三 把详细思路完善一下(纯后端)

    1. 接收参数(手机号,图片验证码,uuid)
    2. 验证参数
        验证手机号
        这三个参数必须有
    3. 验证用户输入的图片验证码和服务器保存的图片验证码一致
        3.1 用户的图片验证码
        3.2 服务器的验证码
        3.3 比对
    4. 先生成一个随机短信码
    5. 先把短信验证码保存起来
        redis key:value
    6. 最后发送


四 确定我们请求方式和路由

    GET
        提取URL的特定部分，如/weather/beijing/2018，可以在服务器端的路由中用正则表达式截取；
            /smscode/mobile/uuid/imagecode/
        查询字符串（query string)，形如key1=value1&key2=value2；
            /smscode/?mobile=xxxx&uuid=xxxx&imagecode=xxxx

        混合的
            /sms_codes/(?P<mobile>1[3-9]\d{9})/?uuid=xxx&imagecode=xxxxx


    POST


"""
import logging
logger = logging.getLogger('django')

class SmsCodeView(View):

    def get(self,request,mobile):
        # 1. 接收参数(手机号,图片验证码,uuid)
        image_code = request.GET.get('image_code')
        uuid=request.GET.get('image_code_id')
        # 2. 验证参数
        #     验证手机号
        #     这三个参数必须有
        if not all([mobile,image_code,uuid]):
            # 响应码
            return http.JsonResponse({'code':RETCODE.NECESSARYPARAMERR,'errormsg':'参数不齐'})
        # 3. 验证用户输入的图片验证码和服务器保存的图片验证码一致
        #     3.1 用户的图片验证码
        #     3.2 服务器的验证码
        try:
            redis_conn = get_redis_connection('code')
            redis_code = redis_conn.get('img_%s'%uuid)

            if redis_code is None:
                return http.JsonResponse({'code':RETCODE.IMAGECODEERR,'errmsg':'验证码过期'})

            # 添加一个删除图片验证码的逻辑
            # 1. 删除可以防止 用户再次比对
            # 2. 从redis数据是保存在内存中,不用的就删除,节省内存空间
            redis_conn.delete('img_%s'%uuid)
        except Exception as e:
            logger.error(e)
            return http.JsonResponse({'code':RETCODE.DBERR,'errmsg':'redis有异常'})

        #     3.3 比对
        # 我们获取redis的数据都是bytes类型
        if redis_code.decode().lower() != image_code.lower():
            return http.JsonResponse({'code':RETCODE.SMSCODERR,'errmsg':'短信验证码错误'})


        # 判断标记位是否为1
        send_flag = redis_conn.get('send_flag_%s'%mobile)

        if send_flag:
            return http.JsonResponse({'code':RETCODE.THROTTLINGERR,'errmsg':'操作太频繁'})

        # 4. 先生成一个随机短信码
        from random import randint
        # 不满6位 补齐
        sms_code =  '%06d'%randint(0,999999)

        # 5. 先把短信验证码保存起来
        #     redis key:value
        #      mobile:value
        # redis_conn.setex(key,secondes,value)
        # redis_conn.setex('sms_%s'%mobile,300,sms_code)

        #① 创建管道
        pipe = redis_conn.pipeline()
        # ②
        # redis_conn.setex('sms_%s'%mobile,SMS_CODE_EXPIRE_TIME,sms_code)
        # redis_conn.setex('send_flag_%s'%mobile,60,1)

        pipe.setex('sms_%s' % mobile, SMS_CODE_EXPIRE_TIME, sms_code)
        pipe.setex('send_flag_%s' % mobile, 60, 1)

        #③ 让管道执行
        pipe.execute()

        # 6. 最后发送
        # 注意： 测试的短信模板编号为1
        # 参数1: 给谁发
        # 参数２：　【云通讯】您使用的是云通讯短信模板，您的验证码是{1}，请于{2}分钟内正确输入
        # 参数３：　模板号　，默认我们选１
        # CCP().send_template_sms(mobile,[sms_code,5],1)

        # 我们的函数 需要通过delay调用 才能添加到 broker(队列)中
        from celery_tasks.sms.tasks import send_sms_code
        # send_sms_code 的参数 平移到 delay中
        send_sms_code.delay(mobile,sms_code)


        return http.JsonResponse({'code':RETCODE.OK,'errmsg':'ok'})


    """
    A: 在吗?
    A: 吃了吗?
    B: 没吃呢?


    A: 在吗? 吃了吗?


    笔友
    信
    北京              上海


    """
