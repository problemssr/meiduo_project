from django import http
from django.core.cache import cache
from django.shortcuts import render

# Create your views here.
from django.views import View

from apps.areas.models import Area
from utils.response_code import RETCODE


class AreasView(View):
    def get(self, request):
        parent_id = request.GET.get('area_id')
        if parent_id is None:
            # 读取省份缓存数据
            province_list = cache.get('province_list')

            if not province_list:
                # 提供省份数据
                provinces = Area.objects.filter(parent_id=None)
                province_list = []
                for item in provinces:
                    province_list.append({
                        'id': item.id,
                        'name': item.name
                    })
                # 存储省份缓存数据
                cache.set('province_list', province_list, 3600)
            return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'ok', 'province_list': province_list})
        else:
            # 读取市或区缓存数据
            sub_list = cache.get('sub_area_' + parent_id)
            if sub_list is None:
                # 市区县
                sub_areas = Area.objects.filter(parent_id=parent_id)
                # [Area,Area,Area]

                sub_list = []
                for sub in sub_areas:
                    sub_list.append({
                        'id': sub.id,
                        'name': sub.name
                    })
                # 储存市或区缓存数据
                cache.set('sub_area_' + parent_id, sub_list, 3600)
            return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'ok', 'sub_data': sub_list})
