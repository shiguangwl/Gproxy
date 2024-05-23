import re
from typing import List, Tuple, Any
from urllib.parse import urlparse, unquote
import requests
from flask import Flask, request, Response
import base64

replace_dict = {
    '$upstream': '$custom_site',
    'https://i.ytimg.com': '/proxy/https://i.ytimg.com'
}


def parserUrl(url):
    parsed_url = urlparse(request.url)
    return {
        "site": parsed_url.scheme + '://' + parsed_url.netloc,
        "path": parsed_url.path,
        "host": parsed_url.netloc
    }


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
    proxyRequest.url_no_site = '/' + '/'.join(request.url.split('/proxy/')[1].split('/')[3:])
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
        raise Exception("未知错误URL：" + upstream_url + "  错误原因：" + str(e))

    if response.status_code >= 400:
        raise Exception(str(response.status_code) + '请求错误URL: ' + upstream_url)
    proxyResponse = ProxyResponse(response)
    proxyResponse.proxyRequest = requestInfo
    for responseHandler in (postHandlers or []):
        proxyResponse = responseHandler(upstream, proxyResponse)

    return proxyResponse


def preHandler(upstream: Upstream, proxyRequest: ProxyRequest) -> ProxyRequest:
    """
    处理请求头的前置处理函数，替换必要请求头信息。
    """
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
    if (('text/html' in proxyResponse.headers['content_type'] and 'utf-8' in proxyResponse.headers[
        'content_type'].lower())
            or ('application/json' in proxyResponse.headers['content_type'])):
        proxyResponse.content = proxyResponse.response.text
        parse = urlparse(proxyResponse.site)
        for key, value in replace_dict.items():
            search_value = (
                key.replace('$upstream', upstream.site).
                replace('$custom_site', proxyResponse.proxyRequest.site).
                replace('$scheme', parse.scheme).
                replace('$host', parse.netloc)
            )
            replace_value = (
                value.replace('$upstream', upstream.site).
                replace('$custom_site', proxyResponse.proxyRequest.site).
                replace('$scheme', parse.scheme).
                replace('$host', parse.netloc)
            )
            # 正则替换
            proxyResponse.content = re.sub(search_value, replace_value, proxyResponse.content)
            # proxyResponse.content = proxyResponse.content.replace(search_value, replace_value)
    return proxyResponse


def postInjectHandler(upstream: Upstream, proxyResponse: ProxyResponse) -> ProxyResponse:
    """
    注入js代码的后置处理函数。
    """
    if 'text/html' in proxyResponse.headers['content_type'] and 'utf-8' in proxyResponse.headers[
        'content_type'].lower():
        # 注入js代码,在最顶部最先执行
        inject_code = """
        <script>
            (function() {
                // Hook for fetch
                const originalFetch = window.fetch;
                window.fetch = function(input, options) {
                    let url;
                    if (typeof input === 'string') {
                        url = input;
                    } else if (input instanceof Request) {
                        url = input.url;
                    } else {
                        throw new Error('Unsupported fetch input type');
                    }
                
                    const parsedUrl = new URL(url, location.origin);
                    if (parsedUrl.origin === location.origin) {
                        // If the request is to the same origin, don't modify the URL
                        return originalFetch(input, options);
                    } else {
                        const modifiedUrl = location.origin + '/proxy/' + parsedUrl.href;
                        if (typeof input === 'string') {
                            return originalFetch(modifiedUrl, options);
                        } else {
                            const modifiedRequest = new Request(modifiedUrl, {
                                ...input,
                                url: modifiedUrl
                            });
                            return originalFetch(modifiedRequest, options);
                        }
                    }
                };
                
                // Hook for XMLHttpRequest
                const originalOpen = XMLHttpRequest.prototype.open;
                XMLHttpRequest.prototype.open = function(method, url, async, user, password) {
                    const parsedUrl = new URL(url, location.origin);
                    if (parsedUrl.origin === location.origin) {
                        // If the request is to the same origin, don't modify the URL
                        return originalOpen.call(this, method, url, async, user, password);
                    } else {
                        const modifiedUrl = location.origin + '/proxy/' + parsedUrl.href;
                        return originalOpen.call(this, method, modifiedUrl, async, user, password);
                    }
                };

            })();
        </script>
        """
        proxyResponse.content = proxyResponse.content.replace('<head>', '<head>' + inject_code)

    return proxyResponse


def preDisableCache(upstream: Upstream, proxyRequest: ProxyRequest):
    """
    禁用缓存的前置处理函数。
    """
    # proxyRequest.headers['Cache-Control'] = 'no-store'
    return proxyRequest


app = Flask(__name__)


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'])
def proxy(path):
    upstream = Upstream('https://www.youtube.com')
    # 封装请求信息
    proxyRequest = requestBaseConvert(request)
    proxyResponse = proxy_handler(
        proxyRequest,
        upstream,
        preHandlers=[
            preHandler,
            preDisableCache
        ],
        postHandlers=[
            postHandler,
            postReplaceContentHandler,
            postInjectHandler
        ]
    )

    headers = [(name, value) for name, value in proxyResponse.headers.items()]
    return Response(proxyResponse.content, proxyResponse.status_code, headers)


@app.route('/proxy/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'])
def allSiteProxy(path):
    print('异步资源请求代理: ' + path)
    upstream = Upstream('/'.join(request.url.split('/proxy/')[1].split('/')[:3]))
    proxyRequest = requestProxyConvert(request)

    # 处理特殊请求 http://www.youtube.com/api/stats/watchtime...
    if 'api/stats/watchtime' in proxyRequest.url_no_site:
        decoded_url = unquote(proxyRequest.url_no_site)
        proxyRequest.url_no_site = (
            decoded_url.replace(proxyRequest.site, upstream.site).
            replace(proxyRequest.host, upstream.host).
            replace('http://','https://'))

    proxyResponse = proxy_handler(
        proxyRequest,
        upstream,
        preHandlers=[
            preHandler,
            preDisableCache
        ],
        postHandlers=[
            postHandler,
            # postReplaceContentHandler,
            # postInjectHandler
        ]
    )

    headers = [(name, value) for name, value in proxyResponse.headers.items()]
    return Response(proxyResponse.content, proxyResponse.status_code, headers)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)

# TODO
# 自动识别
# ajax拦截替换注入
# 缓存处理
