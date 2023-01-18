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
import base64
import pickle

from django_redis import get_redis_connection


def merge_cookie_to_redis(request, user, response):
    # 1获取到cookie数据
    cookie_str = request.COOKIES.get('carts')
    if cookie_str is None:
        return response
    else:
        carts = pickle.loads(base64.b64decode(cookie_str))
    #     carts: {1:{count:10,selected:True},3:{count:10,selected:True}}

    # 2.初始化数据
    # 2.1 hash的字典数据最终要更新到redis中的 {sku_id:count,sku_id:count}
    cookie_hash = {}
    # 2.2 选中的列表和未选中的列表
    selected_ids = []
    remove_selected_ids = []
    # 3.合并之后形成新的数据
    #     3.1 对cookie数据进行遍历
    for sku_id, count_selected_dict in carts.items():
        cookie_hash[sku_id] = count_selected_dict['count']

        if count_selected_dict['selected']:
            selected_ids.append(sku_id)
        else:
            remove_selected_ids.append(sku_id)
    # 4.把新的数据更新到redis中
    redis_conn = get_redis_connection('carts')
    #     {2:20,3:10,1:10}
    # user = request.user
    redis_conn.hmset('carts_%s' % user.id, cookie_hash)
    #     {2,1}
    if len(selected_ids) > 0:
        redis_conn.sadd('selected_%s' % user.id, *selected_ids)

    if len(remove_selected_ids) > 0:
        redis_conn.srem('selected_%s' % user.id, *remove_selected_ids)

    # 5.删除cookie数据
    response.delete_cookie('carts')

    return response
