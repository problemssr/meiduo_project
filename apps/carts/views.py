import json

from django import http
from django.shortcuts import render

# Create your views here.
from django.views import View
from django_redis import get_redis_connection

from apps.goods.models import SKU
from utils.response_code import RETCODE

"""
1.
    京东

    登陆用户可以实现购物车

    未登陆用户可以实现购物车

2.
    登陆用户必须保存的数据是:  user_id(用户id)
                            sku_id(商品id),count(个数),selected(选中状态)

    未登陆用户必须保存的数据是: sku_id(商品id),count(个数),selected(选中状态)


3.
    登陆用户保存在 保存在后端 (mysql/redis)
            Redis
                原则: 尽量少的占用空间

            分析实现:
                hash
                user_id(用户id)

                    sku_id(商品id):count(个数)

                    selected_sku_id:selected(选中状态)

            优化:
                hash:
                        carts_user_id(用户id)

                            sku_id(商品id):count(个数),


                set
                        把选中商品的id保存起来
                       selected_user_id:  selected_id




    未登陆用户保存在  前端(cookie/local storge/session storage)

            Cookie
                sku_id(商品id),count(个数),selected(选中状态)

            {
                'sku_id': {'count':xxx,'selected':true},
                'sku_id': {'count':xxx,'selected':true},
                'sku_id': {'count':xxx,'selected':true},
                'sku_id': {'count':xxx,'selected':true},
            }


4. 对字典数据进行加密(编码)处理

    字典 -->bytes类型 -->base64编码

    carts = {
        '1':{"count":10,"selected":True},
        '2':{"count":20,"selected":False},
    }

    bytes

    json.dumps       将字典转换为 字符串
    json.loads      将字符串转换为字典

    pickle 的操作比json快

    pickle.dumps     将字典转换为 bytes
    pickle.loads      将bytes转换为字典


    base64

        0100 0001   A

        A       A       A                       AAA
      0100 0001  0100 0001  0100 0001  24 b

      010000   010100   000101  000001  24 b
        X       Y           Z       O           XYZO


一 把需求写下来 (前端需要收集什么 后端需要做什么)

二 把大体思路写下来(后端的大体思路)

三 把详细思路完善一下(纯后端)

四 确定我们请求方式和路由


"""
from django.contrib.auth.mixins import LoginRequiredMixin


class CartView(View):
    """
    一 把需求写下来 (前端需要收集什么 后端需要做什么)

        前端需要收集: 商品id,商品数量, 选中是可选的(默认就是选中)
                如果用户登陆了则请求携带session id
                如果用户未登陆了则不请求携带session id

        后端的需求: 新增数据
    二 把大体思路写下来(后端的大体思路)
        接收数据
        验证数据
        数据保存
        返回相应
    三 把详细思路完善一下(纯后端)

        1.接收数据   sku_id,count,
        2.验证数据
        3根据用户是否登陆来保存
        4登陆用户redis
            4.1 连接redis
            4.2 hash
            4.3 set
            4.4 返回相应
        5未登录用户cookie
            5.1  组织数据
            5.2  对数据进行base64处理
            5.3  设置cookie
            5.4 返回相应

    四 确定我们请求方式和路由
        POST    carts/

    """

    # 新增购物车
    def post(self, request):
        # 1.接收数据   sku_id,count,
        data = json.loads(request.body.decode())

        sku_id = data.get('sku_id')
        count = data.get('count')
        # 2.验证数据
        # 2.1 判断参数是否齐全
        if not all([sku_id, count]):
            return http.JsonResponse({'code': RETCODE.PARAMERR, 'errmsg': '参数不齐'})

        # 2.2 判断商品是否存在
        try:
            sku = SKU.objects.get(pk=sku_id)
        except SKU.DoesNotExist:
            return http.JsonResponse({'code': RETCODE.NODATAERR, 'errmsg': "暂无次数据"})
        # 2.3 数量需要是数值
        try:
            count = int(count)
        except Exception as e:
            return http.JsonResponse({'code': RETCODE.PARAMERR, 'errmsg': '参数错误'})
        # 3根据用户是否登陆来保存
        if request.user.is_authenticated:
            # 4登陆用户redis
            #     4.1 连接redis
            redis_conn = get_redis_connection('carts')
            #     4.2 hash
            # redis_conn.hset('carts_%s'%request.user.id,sku_id,count)

            # ① 先创建管道
            pl = redis_conn.pipeline()

            pl.hincrby('carts_%s' % request.user.id, sku_id, count)
            #     4.3 set
            pl.sadd('selected_%s' % request.user.id, sku_id)

            # ③ 执行管道
            pl.execute()

            #     4.4 返回相应
            return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'ok'})

        else:
            # 5未登录用户cookie

            # 5.0  先获取cookie数据,
            cookie_str = request.COOKIES.get('carts')
            # 判断cookie数据是否存在
            if cookie_str is None:
                # 如果cookie数据不存在,先初始化一个 空的carts
                carts = {}
            else:
                # 如果cookie数据存在,对数据进行解码
                # 对数据进行base64解码
                de = base64.b64decode(cookie_str)
                # 再将bytes类型的数据转换为字典
                carts = pickle.loads(de)

            #     5.1  更新数据
            if sku_id in carts:
                # 数量累加
                origin_count = carts[sku_id]['count']
                count += origin_count
                # count = origin_count + count

            carts[sku_id] = {
                'count': count,
                'selected': True
            }

            #     5.2  对数据进行base64处理
            # 5.2.1 将字典转换为bytes类型
            d = pickle.dumps(carts)
            # 5.2.2 将bytes类型的数据进行base64编码
            # bytes
            en = base64.b64encode(d)
            #     5.3  设置cookie
            response = http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'ok'})

            # set_cookie(key,string_value)
            # response.set_cookie('carts',en)
            response.set_cookie('carts', en.decode())
            #     5.4 返回相应

            return response

    """
    一 把需求写下来 (前端需要收集什么 后端需要做什么)

    二 把大体思路写下来(后端的大体思路)

        查询数据
        展示

    三 把详细思路完善一下(纯后端)

        1.获取用户信息,根据用户信息进行判断
        2.登陆用户redis查询
            2.1 连接redis
            2.2 hash   {sku_id:count}
            2.3 set     [sku_id]
            2.4 根据id查询商品详细信息
            2.5 展示
        3.未登录用户cookie查询
            3.1 读取cookie
            3.2 判断carts数据,如果有则解码数据,如果没有则初始化一个字典
                {sku_id: {count:xxx,selected:xxxx}}
            3.3 根据id查询商品信息信息
            3.4 展示




        1.获取用户信息,根据用户信息进行判断
        2.登陆用户redis查询
            2.1 连接redis
            2.2 hash   {sku_id:count}
            2.3 set     [sku_id]

        3.未登录用户cookie查询
            3.1 读取cookie
            3.2 判断carts数据,如果有则解码数据,如果没有则初始化一个字典
                {sku_id: {count:xxx,selected:xxxx}}

        4.根据id查询商品信息信息
        5.展示

    四 确定我们请求方式和路由
        GET     carts/
    """

    def get(self, request):
        # 1.获取用户信息,根据用户信息进行判断
        user = request.user
        if user.is_authenticated:
            # 2.登陆用户redis查询
            #     2.1 连接redis
            redis_conn = get_redis_connection('carts')
            #     2.2 hash   {sku_id:count}
            sku_id_count = redis_conn.hgetall('carts_%s' % user.id)
            #     2.3 set     [sku_id]
            selected_ids = redis_conn.smembers('selected_%s' % user.id)

            # 将redis的数据统一为cookie的格式  v
            # 将cookie的数据统一为redis的格式

            # {sku_id: {count:xxx,selected:xxxx}}
            carts = {}
            # 对字典数据进行遍历,并且进行解包
            for sku_id, count in sku_id_count.items():

                # 判断商品id是否在选中列表中
                if sku_id in selected_ids:
                    selected = True
                else:
                    selected = False
                # 添加新数据
                carts[int(sku_id)] = {
                    'count': int(count),
                    'selected': selected
                }
        else:
            # 3.未登录用户cookie查询
            #     3.1 读取cookie
            cookie_str = request.COOKIES.get('carts')
            #     3.2 判断carts数据,如果有则解码数据,如果没有则初始化一个字典
            if cookie_str is None:
                carts = {}
            else:
                # 将数据进行base64解码
                de = base64.b64decode(cookie_str)
                carts = pickle.loads(de)

        # {sku_id: {count:xxx,selected:xxxx}}
        # 4.根据id查询商品详细信息
        ids = carts.keys()
        # [1,2,3,4]
        # 4.1 计算总价格
        # 4.2 添加商品的选中状态和数量
        skus = SKU.objects.filter(id__in=ids)

        sku_list = []
        # 总数量
        total_count = 0
        # 总价
        total_amount = 0
        # {sku_id: {count:xxx,selected:xxxx}}
        for sku in skus:
            sku_list.append({
                'id': sku.id,
                'name': sku.name,
                'count': carts.get(sku.id).get('count'),
                'selected': str(carts.get(sku.id).get('selected')),  # 将True，转'True'，方便json解析
                'default_image_url': sku.default_image.url,
                'price': str(sku.price),  # 从Decimal('10.2')中取出'10.2'，方便json解析
                'amount': str(sku.price * carts.get(sku.id).get('count')),
            })

            total_count += carts[sku.id]['count']
            total_amount += (sku.price * carts[sku.id]['count'])

        # 5.展示
        context = {
            'cart_skus': sku_list
        }
        return render(request, 'cart.html', context=context)

    """
    一 把需求写下来 (前端需要收集什么 后端需要做什么)

        前端: 要收集sku_id,count,selected 传递给后端
        后端: 更新数据

    二 把大体思路写下来(后端的大体思路)

        指定更新哪里的数据
        接收数据
        验证数据
        更新数据
        返回相应

    三 把详细思路完善一下(纯后端)


        1.接收数据
        2.验证数据
        3.获取用户的信息
        4.登陆用户更新redis数据
            4.1 连接redis
            4.2 hash
            4.3 set
            4.4 返回相应
        5.未登录更新cookie数据
            5.1 获取cart数据,并判断
            5.2 更新指定数据
            5.3 对字典数据进行处理,并设置cookie
            5.4 返回相应


    四 确定我们请求方式和路由

    """

    def put(self, request):
        # 1.接收数据
        data = json.loads(request.body.decode())
        # 2.验证数据
        sku_id = data.get('sku_id')
        count = data.get('count')
        selected = data.get('selected')
        # 2.验证数据
        # 2.1 判断参数是否齐全
        if not all([sku_id, count]):
            return http.JsonResponse({'code': RETCODE.PARAMERR, 'errmsg': '参数不齐'})

        # 2.2 判断商品是否存在
        try:
            sku = SKU.objects.get(pk=sku_id)
        except SKU.DoesNotExist:
            return http.JsonResponse({'code': RETCODE.NODATAERR, 'errmsg': "暂无次数据"})
        # 2.3 数量需要是数值
        try:
            count = int(count)
        except Exception as e:
            return http.JsonResponse({'code': RETCODE.PARAMERR, 'errmsg': '参数错误'})
        # 3.获取用户的信息
        if request.user.is_authenticated:
            # 4.登陆用户更新redis数据
            #     4.1 连接redis
            redis_conn = get_redis_connection('carts')
            #     4.2 hash
            redis_conn.hset('carts_%s' % request.user.id, sku_id, count)
            #     4.3 set
            if selected:
                redis_conn.sadd('selected_%s' % request.user.id, sku_id)
            else:
                redis_conn.srem('selected_%s' % request.user.id, sku_id)
            #     4.4 返回相应
            cart_sku = {
                'id': sku_id,
                'count': count,
                'selected': selected,
                'name': sku.name,
                'default_image_url': sku.default_image.url,
                'price': sku.price,
                'amount': sku.price * count,
            }
            return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'ok', 'cart_sku': cart_sku})

        else:
            # 5.未登录更新cookie数据
            #     5.1 获取cart数据,并判断
            cookie_str = request.COOKIES.get('carts')
            if cookie_str is None:
                carts = {}
            else:
                carts = pickle.loads(base64.b64decode(cookie_str))
            #     5.2 更新指定数据
            # {sku_id: {count:xxxx,selected:xxxx}}
            if sku_id in carts:
                carts[sku_id] = {
                    'count': count,
                    'selected': selected
                }
            #     5.3 对字典数据进行处理,并设置cookie
            en = base64.b64encode(pickle.dumps(carts))
            #     5.4 返回相应
            cart_sku = {
                'id': sku_id,
                'count': count,
                'selected': selected,
                'name': sku.name,
                'default_image_url': sku.default_image.url,
                'price': sku.price,
                'amount': sku.price * count,
            }
            respnse = http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'ok', 'cart_sku': cart_sku})

            respnse.set_cookie('carts', en)

            return respnse

    """
    一 把需求写下来 (前端需要收集什么 后端需要做什么)
        前端需要把商品id传递给后端
        后端把指定的商品删除就可以
    二 把大体思路写下来(后端的大体思路)

        根据id进行删除
        登陆用户删除redis
        未登陆用户删除cookie


    三 把详细思路完善一下(纯后端)

         1.接收数据 sku_id
         2.根据用户信息进行判断
         3.登陆用户删除redis
            3.1 连接redis
            3.2 hash
            3.3 set
            3.4 返回相应
         4.未登陆用户删除cookie
            4.1 读取cookie中的数据,并且判断
            4.2 删除数据
            4.3 字典数据处理,并设置cookie
            4.4 返回相应

    四 确定我们请求方式和路由

    """

    def delete(self, request):
        # 1.接收数据 sku_id
        data = json.loads(request.body.decode())

        sku_id = data.get('sku_id')
        # 2.根据用户信息进行判断
        if request.user.is_authenticated:

            # 3.登陆用户删除redis
            #    3.1 连接redis
            redis_conn = get_redis_connection('carts')
            #    3.2 hash
            redis_conn.hdel('carts_%s' % request.user.id, sku_id)
            #    3.3 set
            redis_conn.srem('selected_%s' % request.user.id, sku_id)
            #    3.4 返回相应
            return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'ok'})
        else:

            # 4.未登陆用户删除cookie
            #    4.1 读取cookie中的数据,并且判断
            cookie_str = request.COOKIES.get('carts')
            if cookie_str is None:
                carts = {}
            else:
                carts = pickle.loads(base64.b64decode(cookie_str))
            #    4.2 删除数据
            if sku_id in carts:
                del carts[sku_id]

            en = base64.b64encode(pickle.dumps(carts))

            #    4.3 字典数据处理,并设置cookie
            response = http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'ok'})
            response.set_cookie('carts', en.decode())

            #    4.4 返回相应
            return response


"""
我们登陆的时候合并 (普通登陆/QQ登陆的时候都能合并)

将cookie数据合并到redis中

1.获取到cookie数据
    carts: {1:{count:10,selected:True},3:{count:10,selected:True}}
2.读取redis的数据
    hash:   {2:20,3:20}
    set     {2,3}
3.合并之后形成新的数据
    3.1 对cookie数据进行遍历

    合并的原则:
        ① cookie中有的,redis中没有的,则将cookie中的数据添加到redis中
        ② cookie中有的,redis中也有,count怎么办?
            count以 cookie为主
        ③ 选中状态以cookie为主

    hash 新增一个 {1:10}
    hash 更新一个 {3:10}

    选中的增加一个 [1,3]
    选中的减少一个 []


4.把新的数据更新到redis中
    {2:20,3:10,1:10}
    {2,1}

5.删除cookie数据


"""

# python manage.py shell
import pickle
import base64

carts = {
    '1': {"count": 10, "selected": True},
    '2': {"count": 20, "selected": False},
}
# 将字典转换为二进制
d = pickle.dumps(carts)

l = pickle.loads(d)

###################################################

# base64
# 将二进制转换为新的编码格式
en = base64.b64encode(d)

# 解码 将编码的数据转换为 正常的数据
de = base64.b64decode(en)
