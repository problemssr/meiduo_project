from django import http
from django.shortcuts import render

# Create your views here.
from django.views import View

from apps.contents.utils import get_categories
from apps.goods.models import SKU, GoodsCategory
from apps.goods.utlis import get_breadcrumb
from utils.response_code import RETCODE

"""

一个页面的需求分析,先从大的方向把流程搞清楚
再把页面中 动态展示的数据 分析出来(需求)

再把一些需求模块化

把需求简单化



我们以列表数据展示为例

一 把需求写下来 (前端需要收集什么 后端需要做什么)
    前端需要必须收集分类id,  排序字段和页码是可选的
    后端就是根据需要查询数据

二 把大体思路写下来(后端的大体思路)

    1.根据分类id,把所有数据都查询出来
    2.如果有排序字段再排序
    3.如果有分页字段再分页

三 把详细思路完善一下(纯后端)

    1.根据分类id,把所有数据都查询出来
    2.如果有排序字段再排序
    3.如果有分页字段再分页

四 确定我们请求方式和路由
        GET list/(?P<category_id>\d+)/(?P<page_num>\d+)/?sort=排序方式

"""
import logging

logger = logging.getLogger('django')


class ListView(View):

    def get(self, request, category_id, page_num):

        # 一.面包屑实现
        """
        我们需要根据当前的分类,来获取它的上级/下级信息

        """
        # ① 获取当前的分类
        try:
            category = GoodsCategory.objects.get(id=category_id)
        except Exception as e:
            logger.error(e)
            return render(request, 'list.html', context={'errmsg': '没有此分类'})
        # ② 获取它的上级/下级
        # 如果是三级　３个信息
        # 如果是二级　２个信息
        # 如果是１级　１个信息
        breadcrumb = get_breadcrumb(category)

        # 二.列表数据

        # 1.如果有排序字段先排序
        sort = request.GET.get('sort')
        # sort = hot 人气 根据 销量排序
        # sort = price 价格 根据 价格排序
        # sort = default 默认 根据 create_time排序
        if sort == 'hot':
            order_filed = 'sales'
        elif sort == 'price':
            order_filed = 'price'
        else:
            order_filed = 'create_time'
            sort = 'default'

        # 2.根据分类id,把所有数据都查询出来
        skus = SKU.objects.filter(category_id=category_id, is_launched=True).order_by(order_filed)

        # 3.如果有分页字段再分页
        try:
            page_num = int(page_num)
        except Exception as e:
            page_num = 0

        # 3.1 导入分页类
        from django.core.paginator import Paginator
        # 3.2 创建分页实例
        paginator = Paginator(skus, per_page=5)
        # 3.3 获取分页数据
        page_skus = paginator.page(page_num)
        # 总页数
        total_page = paginator.num_pages

        context = {
            'category': category,
            'breadcrumb': breadcrumb,
            'sort': sort,  # 排序字段
            'page_skus': page_skus,  # 分页后数据
            'total_page': total_page,  # 总页数
            'page_num': page_num,  # 当前页码
        }

        return render(request, 'list.html', context=context)
