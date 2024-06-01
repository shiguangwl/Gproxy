import json
import os

from entitys import Upstream, ReplaceItem

# 加载配置文件proxy-config.json
# configObj = {}

# configFile = 'proxy-config-xvideos.json'
# configFile = 'proxy-config-pornduce.json'
# configFile = 'proxy-config-pornhub.json'
configFile = 'proxy-config-xhamster.json'
# configFile = 'proxy-config-youtube.json'
with open(os.path.join(os.path.dirname(__file__), configFile), 'r') as file:
    configObj = json.load(file)

# 上游网站的域名.
base_upstream = Upstream(configObj['base_upstream'])
# 拒绝请求列表
deny_request_list = configObj['deny_request']
# 替换规则
replace_list = []
for replaceItem in configObj['replace_list']:
    replace_list.append(
        ReplaceItem(
            replaceItem['search'],
            replaceItem['replace'],
            replaceItem['matchType'],
            replaceItem['urlMatch'],
            replaceItem['urlExclude'],
            replaceItem['contentType']
        )
    )

global_proxy_path = 'proxy' + '-dGltZWhv'

home_path = configObj['home_path']

customHandlers = [
    # TODO 指定以处理器
]
