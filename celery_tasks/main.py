"""
Celery 将这三者串联起来

生产者         队列           消费者

1. 创建celery

2. 设置队列(broker)

3. 设置生产者(任务 task)
        ① 任务的本质就是函数
        ② 这个函数必须要被celery的实例对象的 task装饰器装饰
        ③ 必须调用celery实例对象的自动检测来检测任务

4. 设置消费者(worker)
    celery -A celery实例对象的文件 worker -l info

    celery -A celery_tasks.main worker -l info
"""

# ① 让celery去加载我们当前工程中的配置文件
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "meiduo_mall.settings")

# ② 创建celery实例对象
from celery import Celery

# celery的第一个参数是main
# 习惯上,填写当前脚本的工程名就可以
# 给celery的实例起个名字,这个名字唯一就可以
app = Celery('celery_tasks')

# ③ celery 设置 broker (队列)
# config_from_object 参数: 就是 配置文件的路径
app.config_from_object('celery_tasks.config')

# ④ 让celery自动检测任务
# autodiscover_tasks 参数是 列表
# 列表的元素是: 任务的包路径
app.autodiscover_tasks(['celery_tasks.email'])
