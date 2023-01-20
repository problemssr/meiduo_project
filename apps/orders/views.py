from django.shortcuts import render

# Create your views here.
from django.views import View

"""

一 把需求写下来 (前端需要收集什么 后端需要做什么)

    前端需要把用户信息给我们就可以了

    后端需要展示 地址信息和订单信息

二 把大体思路写下来(后端的大体思路)

        获取登陆用户的地址信息
        获取登陆用户选中的商品信息

三 把详细思路完善一下(纯后端)

        1.获取用户信息
        2.获取登陆用户的地址信息
        3.获取登陆用户选中的商品信息redis
            3.1 连接redis
            3.2 hash(选中和未选中)
            3.3 set
            3.4 对数据进行一下转换,同时我们重新组织数据,
                这个数据只包含选中的商品id和数量
            3.5 根据id查询商品的详细信息
            3.6 统计 总金额和总数量 运费信息


四 确定我们请求方式和路由
        GET     order/place/
"""

import json

from decimal import Decimal
from time import sleep

from django import http
from django.shortcuts import render

# Create your views here.
from django.views import View
from django_redis import get_redis_connection

from apps.goods.models import SKU
from apps.orders.models import OrderInfo, OrderGoods
from apps.users.models import Address
from utils.response_code import RETCODE

"""

一 把需求写下来 (前端需要收集什么 后端需要做什么)

    前端需要把用户信息给我们就可以了

    后端需要展示 地址信息和订单信息

二 把大体思路写下来(后端的大体思路)

        获取登陆用户的地址信息
        获取登陆用户选中的商品信息

三 把详细思路完善一下(纯后端)

        1.获取用户信息
        2.获取登陆用户的地址信息
        3.获取登陆用户选中的商品信息redis
            3.1 连接redis
            3.2 hash(选中和未选中)
            3.3 set
            3.4 对数据进行一下转换,同时我们重新组织数据,
                这个数据只包含选中的商品id和数量
            3.5 根据id查询商品的详细信息
            3.6 统计 总金额和总数量 运费信息


四 确定我们请求方式和路由
        GET     order/place/
"""
from django.contrib.auth.mixins import LoginRequiredMixin
import logging

logger = logging.getLogger('django')


class PlaceOrderView(LoginRequiredMixin, View):

    def get(self, request):
        # 1.获取用户信息
        user = request.user
        # 2.获取登陆用户的地址信息
        try:
            addresses = Address.objects.filter(user=user, is_deleted=False)
        except Exception as e:
            logger.error(e)
            return render(request, 'place_order.html', context={'errmsg': '地址查询失败'})
        # 3.获取登陆用户选中的商品信息redis

        #     3.1 连接redis
        redis_conn = get_redis_connection('carts')
        #     3.2 hash(选中和未选中)
        id_count = redis_conn.hgetall('carts_%s' % user.id)
        #     3.3 set
        selected_ids = redis_conn.smembers('selected_%s' % user.id)

        #     3.4 对数据进行一下转换,同时我们重新组织数据,
        #         这个数据只包含选中的商品id和数量
        # {sku_id:count,sku_id:count}
        selected_carts = {}
        for id in selected_ids:
            selected_carts[int(id)] = int(id_count[id])
        #     3.5 根据id查询商品的详细信息
        ids = selected_carts.keys()
        # [id,id,...]
        skus = SKU.objects.filter(id__in=ids)
        # [sku,sku,sku]
        #     3.6 统计 总金额和总数量 运费信息
        total_count = 0  # 总数量
        total_amount = 0  # 总金额
        freight = 10  # 运费
        # 循环变量 来添加 商品数量小计和金额 以及统计 总金额和总数量
        for sku in skus:
            # 每个商品的数量小计和金额小计
            sku.count = selected_carts[sku.id]
            sku.amount = (sku.count * sku.price)

            # 总金额和总数量
            total_count += selected_carts[sku.id]
            total_amount += (sku.count * sku.price)

        context = {
            'addresses': addresses,
            'skus': skus,
            'total_count': total_count,
            'total_amount': total_amount,
            'freight': freight,
            'payment_amount': total_amount + freight
        }

        return render(request, 'place_order.html', context=context)


"""
一 把需求写下来 (前端需要收集什么 后端需要做什么)
    前端: 需要收集 用户信息(随着请求cookie传递 sessionid 过来的)
                    地址信息,支付方式

    后端: 需要生成订单信息和订单商品信息

二 把大体思路写下来(后端的大体思路)

    先订单信息
    再订单商品信息

三 把详细思路完善一下(纯后端)
        1.订单信息
            1.1 获取用户信息
            1.2 获取地址信息
            1.3 获取支付方式
            1.4 生成订单id
            1.5 组织总金额 0 总数量 0 运费
            1.6 组织订单状态
        2.订单商品信息(我们从redis中获取选中的商品信息)
            2.1 连接redis
            2.2 hash
            2.3 set
            2.4 类型转换,转换过程中重新组织数据
                选中的数据
                {sku_id:count,sku_id:count}
            2.5 获取选中的商品id  [1,2,3]
            2.6 遍历id
                2.7 查询
                2.8 判断库存
                2.9 库存减少,销量增加
                2.10 保存商品信息
                2.11 累加计算 总金额和总数量
        3. 保存订单信息的修改
        4. 清除redis中选中商品的信息



四 确定我们请求方式和路由
    POST        /order/
"""


class OrderView(View):

    def post(self, request):

        # 这里省略了很多操作,这些操作不需要事务

        # 1.订单信息
        #     1.1 获取用户信息
        user = request.user
        data = json.loads(request.body.decode())
        address_id = data.get('address_id')
        pay_method = data.get('pay_method')
        if not all([address_id, pay_method]):
            return http.JsonResponse({'code': RETCODE.PARAMERR, 'errmsg': '参数不全'})
        #     1.2 获取地址信息
        try:
            address = Address.objects.get(pk=address_id)
        except Address.DoesNotExist:
            return http.JsonResponse({'code': RETCODE.NODATAERR, 'errmsg': '地址不存在'})
        #     1.3 获取支付方式
        # if  pay_method not in [1,2] 这么写是对的,但是 1 和 2 不知道确切的含义
        # 1   OrderInfo.PAY_METHODS_ENUM['CASH']
        # 只是增加了代码的可读性
        if pay_method not in [OrderInfo.PAY_METHODS_ENUM['CASH'], OrderInfo.PAY_METHODS_ENUM['ALIPAY']]:
            return http.JsonResponse({'code': RETCODE.PARAMERR, 'errmsg': '参数错误'})

        #     1.4 生成订单id
        # order_id = 年月日时分秒 + 9位用户id
        from django.utils import timezone
        # Y year
        # m month
        # d day
        # H hour
        # M minute
        # S sencode
        #
        order_id = timezone.localtime().strftime('%Y%m%d%H%M%S') + '%09d' % user.id

        #     1.5 组织总金额 0 总数量 0 运费
        # 金钱我们最好使用 Decimal类型
        # mysql: 浮点型: float double decimal
        # Decimal 就是能够确保货比的精度
        # 100/3 33.33       33.33*3 = 99.99
        #               33.33 33.33 33.34

        total_count = 0
        total_amout = Decimal('0')
        freight = Decimal('10.00')
        #     1.6 组织订单状态
        # 订单状态和支付方式关联
        # 1 pay_method == 1 表示 货到付款  -->待发货
        # 2 pay_method == 2 表示 支付宝    -->待支付
        # if pay_method == 1:
        #     status = 2
        # else:
        #     status = 1

        if pay_method == OrderInfo.PAY_METHODS_ENUM['CASH']:
            status = OrderInfo.ORDER_STATUS_ENUM['UNSEND']
        else:
            status = OrderInfo.ORDER_STATUS_ENUM['UNPAID']

        from django.db import transaction
        with transaction.atomic():

            # 一  事务的回滚点
            point_id = transaction.savepoint()

            order = OrderInfo.objects.create(
                order_id=order_id,
                user=user,
                address=address,
                total_count=total_count,
                total_amount=total_amout,
                freight=freight,
                pay_method=pay_method,
                status=status
            )

            # 2.订单商品信息(我们从redis中获取选中的商品信息)
            #     2.1 连接redis
            redis_conn = get_redis_connection('carts')
            #     2.2 连接redis
            redis_conn = get_redis_connection('carts')
            #      hash(选中和未选中)
            id_count = redis_conn.hgetall('carts_%s' % user.id)
            #      set
            selected_ids = redis_conn.smembers('selected_%s' % user.id)

            #     2.4 对数据进行一下转换,同时我们重新组织数据,
            #         这个数据只包含选中的商品id和数量
            # {sku_id:count,sku_id:count}
            selected_carts = {}
            for id in selected_ids:
                selected_carts[int(id)] = int(id_count[id])

            #     2.5 获取选中的商品id  [1,2,3]
            ids = selected_carts.keys()
            # skus = SKU.objects.filter(id__in=ids)

            print('~~~~~~~~~~~~~~~~~~~~~~')
            #     2.6 遍历id
            for id in ids:
                #         2.7 查询
                sku = SKU.objects.get(id=id)
                #         2.8 判断库存
                # 获取购买的数量
                count = selected_carts[sku.id]
                if sku.stock < count:
                    # 二 如果失败 回滚
                    transaction.savepoint_rollback(point_id)

                    return http.JsonResponse({'code': RETCODE.STOCKERR, 'errmsg': '库存不足'})
                #         2.9 库存减少,销量增加
                # sleep(10)
                #
                # sku.stock -= count
                # sku.sales += count
                # sku.save()

                # 用乐观来实现

                # 在更新的时候判断此时的库存是否是之前查询出的库存一致
                # 一致则更新成功 返回1
                # 不一致则不更新 返回0
                print('----------------------')
                # 1. 记录之前的库存
                old_stock = sku.stock

                # 2.计算更新的数据
                new_stock = sku.stock - count
                new_sales = sku.sales + count
                # 3.更新的时候判断

                result = SKU.objects.filter(id=sku.id, stock=old_stock).update(stock=new_stock, sales=new_sales)

                if result == 0:
                    print('下单失败')
                    # 下单失败
                    transaction.savepoint_rollback(point_id)

                    return http.JsonResponse({'code': RETCODE.STOCKERR, 'errmsg': '下单失败'})

                #         2.10 保存商品信息
                OrderGoods.objects.create(
                    order=order,
                    sku=sku,
                    count=count,
                    price=sku.price
                )
                #         2.11 累加计算 总金额和总数量
                order.total_count += count
                order.total_amount += (count * sku.price)
                #
            # 3. 保存订单信息的修改
            order.save()

            # 三 提交事务
            transaction.savepoint_commit(point_id)

        # 4. 清除redis中选中商品的信息
        # 暂缓实现 我们要重复很多次

        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'ok', 'order_id': order_id})


class OrderSuccessView(LoginRequiredMixin, View):
    """提交订单成功"""

    def get(self, request):
        order_id = request.GET.get('order_id')
        payment_amount = request.GET.get('payment_amount')
        pay_method = request.GET.get('pay_method')

        context = {
            'order_id': order_id,
            'payment_amount': payment_amount,
            'pay_method': pay_method
        }
        return render(request, 'order_success.html', context)
