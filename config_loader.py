from entitys import Upstream, ReplaceItem
import json
# 加载配置文件proxy-config.json
# configObj = {}
with open('proxy-config-youtube' + '.json', 'r') as file:
    configObj = json.load(file)

# 上游网站的域名.
base_upstream = Upstream(configObj['base_upstream'])
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
