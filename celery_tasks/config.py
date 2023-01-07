# 我们选择的是redis作为我们的 队列
# 选择redis的 14号库
broker_url = "redis://127.0.0.1/14"
# 结果选择15号库
result_backend = "redis://127.0.0.1/15"