def get_breadcrumb(category):
    # ② 获取它的上级/下级
    # 如果是三级　３个信息
    # 如果是二级　２个信息
    # 如果是１级　１个信息
    breadcrumb = {
        'cat1': '',
        'cat2': '',
        'cat3': ''
    }

    # 判断传递过来的分类是几级
    # 当前就三级
    if category.parent is None:
        # 一级
        breadcrumb['cat1'] = category
        pass
    elif category.subs.count() == 0:
        # 三级
        breadcrumb['cat1'] = category.parent.parent
        breadcrumb['cat2'] = category.parent
        breadcrumb['cat3'] = category
    else:
        # 二级
        breadcrumb['cat1'] = category.parent
        breadcrumb['cat2'] = category

    return breadcrumb
