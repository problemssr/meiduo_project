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


"""
一 把需求写下来 (前端需要收集什么 后端需要做什么)

    前端: 需要把分类id传递给后端
    后端: 根据分类id查询数据

二 把大体思路写下来(后端的大体思路)

    1.获取分类id
    2.查询是否有当前分类
    3.根据分类去查询指定的数据,并进行排序,排序之后获取n条
    4.ajax 把对象列表转换为字典列表
三 把详细思路完善一下(纯后端)

     1.获取分类id
    2.查询是否有当前分类
    3.根据分类去查询指定的数据,并进行排序,排序之后获取n条
    4.ajax 把对象列表转换为字典列表

四 确定我们请求方式和路由
    GET     hot/?cat=xxxx
            hot/cat_id/
"""


class HotView(View):

    def get(self, request, category_id):
        #  1.获取分类id
        # 2.查询是否有当前分类
        try:
            category = GoodsCategory.objects.get(id=category_id)
        except Exception as e:
            return http.JsonResponse({'code': RETCODE.NODATAERR, 'errmsg': '暂无此分类'})
        # 3.根据分类去查询指定的数据,并进行排序,排序之后获取n条
        skus = SKU.objects.filter(category=category, is_launched=True).order_by('-sales')[:2]
        # 4.ajax 把对象列表转换为字典列表
        skus_list = []
        for sku in skus:
            skus_list.append({
                'id': sku.id,
                'default_image_url': sku.default_image.url,
                'name': sku.name,
                'price': sku.price
            })

        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'ok', 'hot_skus': skus_list})


"""
搜索引擎的原理: 类似于新华字典的索引

    我是中国人 --> 搜索引擎 --> 进行分词处理 --> (我,是,中国,中国人,国人)

    我       -->   我是中国人 这条记录
    中国      -->

    我是中
    国人

全文检索(搜索)  --> 借助于 搜索引擎 (进行分词处理) --> 建立搜索词 和 搜索结果的对应关系

    我                 (我,是,中国,中国人,国人)           我是中国人



1. 我们的搜索不使用like,因为like 查询效率低, 多个字段查询不方便

2. 我们搜索使用全文检索

3. 全文检索 需要使用 搜索引擎

4. 我们的搜索引擎使用 elasticsearch


使用 elasticsearch 实现全文检索


数据          haystack          elasticsearch

"""


class DetailView(View):
    def get(self, request, sku_id):
        """提供商品详情页"""
        # 获取当前sku的信息
        try:
            sku = SKU.objects.get(id=sku_id)
        except SKU.DoesNotExist:
            return render(request, '404.html')
        # 查询商品频道分类
        categories = get_categories()
        # 查询面包屑导航
        breadcrumb = get_breadcrumb(sku.category)

        # 构建当前商品的规格键
        sku_specs = sku.specs.order_by('spec_id')
        sku_key = []
        for spec in sku_specs:
            sku_key.append(spec.option.id)
        # 获取当前商品的所有SKU
        skus = sku.spu.sku_set.all()
        # 构建不同规格参数（选项）的sku字典
        spec_sku_map = {}
        for s in skus:
            # 获取sku的规格参数
            s_specs = s.specs.order_by('spec_id')
            # 用于形成规格参数-sku字典的键
            key = []
            for spec in s_specs:
                key.append(spec.option.id)
            # 向规格参数-sku字典添加记录
            spec_sku_map[tuple(key)] = s.id
        # 获取当前商品的规格信息
        goods_specs = sku.spu.specs.order_by('id')
        # 若当前sku的规格信息不完整，则不再继续
        if len(sku_key) < len(goods_specs):
            return
        for index, spec in enumerate(goods_specs):
            # 复制当前sku的规格键
            key = sku_key[:]
            # 该规格的选项
            spec_options = spec.options.all()
            for option in spec_options:
                # 在规格参数sku字典中查找符合当前规格的sku
                key[index] = option.id
                option.sku_id = spec_sku_map.get(tuple(key))
            spec.spec_options = spec_options

        # 渲染页面
        context = {
            'categories': categories,
            'breadcrumb': breadcrumb,
            'sku': sku,
            'specs': goods_specs,
        }

        return render(request, 'detail.html', context)
