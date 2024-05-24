import re
from typing import List, Tuple, Any
from urllib.parse import urlparse, unquote
import requests
from flask import Flask, request, Response, abort

import config_loader
from common.CustomLogger import logger
from entitys import ReplaceItem, ProxyRequest, ProxyResponse, Upstream, requestBaseConvert, \
    requestProxyConvert

# 上游网站的域名.
base_upstream = config_loader.base_upstream
# 替换规则
replace_list = config_loader.replace_list
# 读取注入inject.js
js_content = ''
with open('./static/inject.js', 'r') as file:
    js_content = file.read()

def proxy_handler(
        requestInfo: ProxyRequest,
        upstream: Upstream,
        preHandlers=None,
        postHandlers=None
) -> ProxyResponse:
    """
    处理代理请求的主函数。

    参数:
    - requestInfo: ProxyRequest对象，包含客户端请求的所有信息。
    - preHandlers: 一个可选的前置处理函数列表，每个函数接收一个ProxyRequest对象并返回处理后的ProxyRequest对象。
    - postHandlers: 一个可选的后置处理函数列表，每个函数接收一个响应对象并返回处理后的响应对象。

    返回值:
    - ProxyResponse对象，包含从上游服务器收到的响应信息。
    """
    # 执行前置处理函数
    if postHandlers is None:
        postHandlers = []
    if preHandlers is None:
        preHandlers = []
    for requestHandler in (preHandlers or []):
        requestInfo = requestHandler(upstream, requestInfo)
    upstream_url = upstream.site + requestInfo.url_no_site
    # 向上游服务器发送请求并接收响应
    try:
        response = requests.request(
            method=requestInfo.method,
            url=upstream_url,
            headers=requestInfo.headers,
            data=requestInfo.data,
            cookies=requestInfo.cookies,
            allow_redirects=False
        )
    except requests.exceptions.RequestException as e:
        # 打印日志抛出错误原因
        logger.error(f'未知错误URL: {upstream_url} 错误原因: {e}')
        abort(500)

    if response.status_code >= 400:
        logger.warning(f'请求响应异常URL: {upstream_url} HTTP状态码: {response.status_code}')
        abort(response.status_code)
    proxyResponse = ProxyResponse(response)
    proxyResponse.proxyRequest = requestInfo
    for responseHandler in (postHandlers or []):
        proxyResponse = responseHandler(upstream, proxyResponse)

    return proxyResponse


def preHandler(upstream: Upstream, proxyRequest: ProxyRequest) -> ProxyRequest:
    """
    处理请求头的前置处理函数，替换必要请求头信息。
    """
    if 'Host' in proxyRequest.headers.keys():
        proxyRequest.headers['Host'] = upstream.host
    if 'Referer' in proxyRequest.headers.keys():
        proxyRequest.headers['Referer'] = proxyRequest.headers['Referer'].replace(proxyRequest.site, upstream.site)
    if 'Origin' in proxyRequest.headers.keys():
        proxyRequest.headers['Origin'] = proxyRequest.headers['Origin'].replace(proxyRequest.site, upstream.site)

    return proxyRequest


def postHandler(upstream: Upstream, proxyResponse: ProxyResponse) -> ProxyResponse:
    """
    处理响应的后置处理函数，替换必要响应信息。
    """

    excluded_headers = ['content-encoding', 'transfer-encoding', 'content-length', 'connection']
    # 移除不必要的头信息
    headers = {name: value for name, value in proxyResponse.headers.items() if name.lower() not in excluded_headers}
    headers['access-control-allow-origin'] = '*'
    headers['access-control-allow-credentials'] = 'true'
    headers['content_type'] = proxyResponse.headers.get('content-type', '')
    # 替换当前域名的从定向
    if proxyResponse.is_redirect:
        location = proxyResponse.headers.get('Location', '')
        location = location.replace(upstream.site, proxyResponse.proxyRequest.site)
        headers['Location'] = location

    proxyResponse.headers = headers
    return proxyResponse


def postReplaceContentHandler(upstream: Upstream, proxyResponse: ProxyResponse) -> ProxyResponse:
    """
    替换响应内容的后置处理函数。
    """
    # 匹配的url
    url_no_site = proxyResponse.proxyRequest.url_no_site
    # 请求返回类型
    content_type = proxyResponse.headers.get('content-type', '')
    for replaceItem in replace_list:
        # 先匹配URL，如果urlMatch和urlExclude都不匹配则继续
        if replaceItem.urlMatch is not None and re.match(replaceItem.urlMatch, url_no_site) is None:
            continue
        if replaceItem.urlExclude is not None and re.match(replaceItem.urlExclude, url_no_site) is not None:
            continue
        # 检查内容类型是否匹配
        if replaceItem.contentType is not None and replaceItem.contentType.lower() not in content_type.lower():
            continue
        # 处理字符串匹配 1 为字符串匹配 2 为正则匹配
        # 判断proxyResponse.content是否为字符串
        if not isinstance(proxyResponse.content, str):
            proxyResponse.content = proxyResponse.response.text
        search_value = replaceKeyword(replaceItem.search, upstream, proxyResponse)
        replace_value = replaceKeyword(replaceItem.replace, upstream, proxyResponse)
        if replaceItem.matchType == 1:
            proxyResponse.content = proxyResponse.content.replace(search_value, replace_value)
        else:
            proxyResponse.content = re.sub(search_value, replace_value, proxyResponse.content)
    return proxyResponse


# 处理关键词替换
def replaceKeyword(value, upstream, proxyResponse):
    parse = urlparse(proxyResponse.site)
    replace_value = (
        # $upstream 替换为上游域名
        value.replace('$upstream', upstream.site).
        # $custom_site 替换为请求协议域名
        replace('$custom_site', proxyResponse.proxyRequest.site).
        # $scheme 替换为协议
        replace('$scheme', parse.scheme).
        # $host 替换为域名
        replace('$host', parse.netloc).
        replace('$proxy', '/' + config_loader.global_proxy_path +  '/')
    )
    return replace_value


def postInjectHandler(upstream: Upstream, proxyResponse: ProxyResponse) -> ProxyResponse:
    """
    注入js代码的后置处理函数。
    """
    if 'text/html' in proxyResponse.headers['content_type'] and 'utf-8' in proxyResponse.headers[
        'content_type'].lower():
        # 注入js代码,在最顶部最先执行
        inject_code = f"<script>{js_content}</script>"
        proxyResponse.content = proxyResponse.content.replace('<head>', '<head>' + inject_code)

    return proxyResponse


def preDisableCache(upstream: Upstream, proxyRequest: ProxyRequest):
    """
    禁用缓存的前置处理函数。
    """
    proxyRequest.headers['Cache-Control'] = 'no-store'
    return proxyRequest


app = Flask(__name__)


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'])
def proxy(path):
    # 封装请求信息
    proxyRequest = requestBaseConvert(request)
    proxyResponse = proxy_handler(
        proxyRequest,
        base_upstream,
        preHandlers=[
            CustomHomePathHandler(config_loader.home_path),
            preHandler,
            # preDisableCache
        ],
        postHandlers=[
            postHandler,
            postReplaceContentHandler,
            postInjectHandler
        ]
    )

    return Response(proxyResponse.content, proxyResponse.status_code, proxyResponse.headers)


@app.route(f'/{config_loader.global_proxy_path}/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'])
def allSiteProxy(path):

    # http://192.168.0.6/proxy/https://www.youtube.com/watch/dddd?v=JGwWNGJdvx8  => https://www.youtube.com
    upstream = Upstream('/'.join(request.url.split(f'/{config_loader.global_proxy_path}/')[1].split('/')[:3]))
    proxyRequest = requestProxyConvert(request)

    # # 处理特殊请求 http://www.youtube.com/api/stats/watchtime...
    # if 'api/stats/watchtime' in proxyRequest.url_no_site:
    #     decoded_url = unquote(proxyRequest.url_no_site)
    #     proxyRequest.url_no_site = (
    #         decoded_url.replace(proxyRequest.site, upstream.site).
    #         replace(proxyRequest.host, upstream.host).
    #         replace('http://','https://'))

    proxyResponse = proxy_handler(
        proxyRequest,
        upstream,
        preHandlers=[
            preHandler,
            # preDisableCache
        ],
        postHandlers=[
            postHandler,
            postReplaceContentHandler,
            # postInjectHandler
        ]
    )

    return Response(proxyResponse.content, proxyResponse.status_code, proxyResponse.headers)


def CustomHomePathHandler(path):
    def homeHandler(upstream: Upstream, proxyRequest: ProxyRequest) -> ProxyRequest:
        """
        处理porn主页的前置处理函数，将主页重定向到中文页面。
        """
        if proxyRequest.path == '/':
            proxyRequest.path = path
            proxyRequest.url_no_site = path
        return proxyRequest
    return homeHandler



if __name__ == '__main__':
    # 关闭调试模式
    app.debug = True
    app.run(host='0.0.0.0', port=80)

# TODO
# 自动识别
# 缓存处理

# Complete
# ajax拦截替换注入
