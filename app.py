from urllib.parse import urlparse
import requests
from flask import Flask, request, Response


replace_dict = {
    '$upstream': '$custom_site',
    r'https:\/\/theporndude.com': r'$scheme:\/\/$host'
}

class Upstream:
    def __init__(self, url):
        parsed_url = urlparse(url)
        self.url = url
        self.site = parsed_url.scheme + '://' + parsed_url.netloc
        self.path = parsed_url.path
        self.host = parsed_url.netloc


class ProxyRequest:
    def __init__(self, request):
        parsed_url = urlparse(request.url)
        self.url = request.url
        self.site = parsed_url.scheme + '://' + parsed_url.netloc
        self.method = request.method
        self.headers = {key: value for key, value in request.headers}
        self.cookies = request.cookies
        self.path = request.path
        self.data = request.get_data()
        self.upstream_url = upstream.site + self.url.replace(self.site, '')


class ProxyResponse:
    def __init__(self, response):
        self.response = response
        self.content = response.content
        self.status_code = response.status_code
        self.headers = response.raw.headers
        self.is_redirect = response.is_redirect
        parsed_url = urlparse(response.url)
        self.site = parsed_url.scheme + '://' + parsed_url.netloc
        self.request_site = None
        self.proxyRequest = None


def proxy_handler(
        requestInfo: ProxyRequest,
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
        requestInfo = requestHandler(requestInfo)
    # 向上游服务器发送请求并接收响应
    response = requests.request(
        method=requestInfo.method,
        url=requestInfo.upstream_url,
        headers=requestInfo.headers,
        data=requestInfo.data,
        cookies=requestInfo.cookies,
        allow_redirects=False
    )
    proxyResponse = ProxyResponse(response)
    proxyResponse.request_site = requestInfo.site
    proxyResponse.proxyRequest = requestInfo
    for responseHandler in (postHandlers or []):
        proxyResponse = responseHandler(proxyResponse)

    return proxyResponse


def preHandler(proxyRequest: ProxyRequest) -> ProxyRequest:
    """
    处理请求头的前置处理函数，替换必要请求头信息。
    """
    proxyRequest.headers['Host'] = upstream.host
    if 'Referer' in proxyRequest.headers.keys():
        proxyRequest.headers['Referer'] = proxyRequest.headers['Referer'].replace(proxyRequest.site, upstream.site)
    if 'Origin' in proxyRequest.headers.keys():
        proxyRequest.headers['Origin'] = proxyRequest.headers['Origin'].replace(proxyRequest.site, upstream.site)

    return proxyRequest


def postHandler(proxyResponse: ProxyResponse) -> ProxyResponse:
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
        location = location.replace(upstream.site, proxyResponse.request_site)
        headers['Location'] = location

    proxyResponse.headers = headers
    return proxyResponse


def postReplaceContentHandler(proxyResponse: ProxyResponse) -> ProxyResponse:
    """
    替换响应内容的后置处理函数。
    """
    if (('text/html' in proxyResponse.headers['content_type'] and 'UTF-8' in proxyResponse.headers['content_type'])
            or ('application/json' in proxyResponse.headers['content_type'])):
        proxyResponse.content = proxyResponse.response.text
        parse = urlparse(proxyResponse.request_site)
        for key, value in replace_dict.items():
            search_value = (
                key.replace('$upstream', upstream.site).
                replace('$custom_site', proxyResponse.request_site).
                replace('$scheme', parse.scheme).
                replace('$host', parse.netloc)
            )
            replace_value = (
                value.replace('$upstream', upstream.site).
                replace('$custom_site', proxyResponse.request_site).
                replace('$scheme', parse.scheme).
                replace('$host', parse.netloc)
            )
            proxyResponse.content = proxyResponse.content.replace(search_value, replace_value)





    return proxyResponse


def preDisableCache(proxyRequest: ProxyRequest):
    """
    禁用缓存的前置处理函数。
    """
    proxyRequest.headers['Cache-Control'] = 'no-store'
    return proxyRequest


app = Flask(__name__)
upstream = Upstream('https://theporndude.com')



@app.route('/', defaults={'path': ''})
@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'])
def proxy(path):
    # 封装请求信息
    proxyRequest = ProxyRequest(request)
    proxyResponse = proxy_handler(
        proxyRequest,
        preHandlers=[
            preHandler,
            preDisableCache
        ],
        postHandlers=[
            postHandler,
            postReplaceContentHandler
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
