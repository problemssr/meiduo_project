from django.shortcuts import render

# Create your views here.
from django.views import View

from apps.contents.models import ContentCategory
from apps.contents.utils import get_categories


class IndexView(View):

    def get(self, request):
        """
         # 1.分类信息
         # 2.楼层信息
        """
        # 1.分类信息 分类信息在其他页面也会出现,我们应该直接抽取为一个方法
        # 查询商品频道和分类
        categories = get_categories()

        # 2.楼层信息
        contents = {}
        content_categories = ContentCategory.objects.all()
        for cat in content_categories:
            contents[cat.key] = cat.content_set.filter(status=True).order_by('sequence')

        # 渲染模板的上下文
        context = {
            'categories': categories,
            'contents': contents,
        }

        return render(request, 'index.html', context=context)
