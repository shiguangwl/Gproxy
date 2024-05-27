# Gproxy

基于python,flask,requests 实现网站全局代理

# 来自GPT注释:
## inject.js
包含了一些JavaScript代码，这些代码会被注入到返回给客户端的HTML页面中。这些代码的主要功能是修改页面中的异步HTTP请求，将这些请求的URL修改为通过代理服务器的URL。
## proxy-config-xxx.json
这个文件包含了一些配置信息，例如上游服务器的URL，以及一些替换规则。这些替换规则定义了在处理请求和响应时，应该如何修改其中的内容。
## app.py
这个文件是项目的主要部分，它定义了一个Flask应用。这个应用有两个路由，一个用于处理对根路径的请求，另一个用于处理对/proxy-***/路径的请求。对于每个请求，它都会创建一个ProxyRequest对象，然后调用proxy_handler函数处理这个请求。proxy_handler函数会将请求转发到上游服务器，并将上游服务器的响应返回给客户端。在这个过程中，它还会调用一些处理函数对请求和响应进行处理。
## config_loader.py
这个文件负责加载proxy-config-pornduce.json文件中的配置信息，并将这些信息存储在全局变量中。


# 配置文件示例
```
{
  // 目标站
  "base_upstream": "https://www.youtube.com",
  // 主页反代路径即当访问 '/' 会代理到挡墙路径
  "home_path" : "/",
  // 替换规则
  "replace_list": [
    {
      "search": "$upstream",
      "replace": "$custom_site",
      "matchType": 1,// 2:正则 1:字符串
      "urlMatch": null,// 匹配url
      "urlExclude": null,// 排除url
      "contentType": null // 匹配content-type
    },
    {
        "search": "https://i.ytimg.com",
        "replace": "$PROXY/https://i.ytimg.com", // 走代理
        "matchType": 1,
        "urlMatch": null,
        "urlExclude": null,
        "contentType": null
    }
  ]
}
....
```
