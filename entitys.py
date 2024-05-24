from urllib.parse import urlparse

from pip._internal.utils.misc import enum

import config_loader


class Upstream:
    def __init__(self, url):
        parsed_url = urlparse(url)
        # 原始url
        self.url = url
        # 协议和域名
        self.site = parsed_url.scheme + '://' + parsed_url.netloc
        # 路径
        self.path = parsed_url.path
        # 域名
        self.host = parsed_url.netloc


class ReplaceItem:
    def __init__(
            self,
            # 需要替换的内容
            search,
            # 替换的内容
            replace,
            # 匹配类型 1 为字符串匹配 2 为正则匹配
            matchType,
            # 匹配的url 正则匹配
            urlMatch=None,
            # 排除的url 正则匹配
            urlExclude=None,
            # 需要替换的内容类型
            contentType=None
    ):
        self.search: str = search
        self.replace: str = replace
        self.matchType: int = matchType
        self.urlMatch: str = urlMatch
        self.urlExclude: str = urlExclude
        self.contentType: str = contentType


class ProxyRequest:
    # 原始请求域名
    site = None
    # host
    host = None
    # url除去site部分
    url_no_site = None
    # 请求方式
    method = None
    # 请求头
    headers = None
    # 请求cookies
    cookies = None
    # 请求路径
    path = None
    # 请求数据
    data = None


# 处理基本请求的转换
def requestBaseConvert(request) -> ProxyRequest:
    proxyRequest = ProxyRequest()
    parsed_url = urlparse(request.url)
    proxyRequest.site = parsed_url.scheme + '://' + parsed_url.netloc
    proxyRequest.host = parsed_url.netloc
    proxyRequest.url_no_site = parsed_url.path + ('?' + parsed_url.query if parsed_url.query else '')
    proxyRequest.method = request.method
    proxyRequest.headers = {key: value for key, value in request.headers}
    proxyRequest.cookies = request.cookies
    proxyRequest.path = request.path
    proxyRequest.data = request.get_data()
    return proxyRequest


# 处理代理请求的转换
def requestProxyConvert(request) -> ProxyRequest:
    proxyRequest = ProxyRequest()
    parsed_url = urlparse(request.url)
    proxyRequest.site = parsed_url.scheme + '://' + parsed_url.netloc
    # http://192.168.0.6/proxy/https://www.youtube.com/watch/dddd?v=JGwWNGJdvx8  => /watch/dddd?v=JGwWNGJdvx8
    proxyRequest.host = parsed_url.netloc
    proxyRequest.url_no_site = '/' + '/'.join(request.url.split('/'+config_loader.global_proxy_path+'/')[1].split('/')[3:])
    proxyRequest.method = request.method
    proxyRequest.headers = {key: value for key, value in request.headers}
    proxyRequest.cookies = request.cookies
    proxyRequest.path = proxyRequest.url_no_site.split('?')[0]
    proxyRequest.data = request.get_data()

    return proxyRequest


class ProxyResponse:
    def __init__(self, response):
        self.response = response
        self.content = response.content
        self.status_code = response.status_code
        self.headers = response.raw.headers
        self.is_redirect = response.is_redirect
        parsed_url = urlparse(response.url)
        self.site = parsed_url.scheme + '://' + parsed_url.netloc
        self.proxyRequest = None
