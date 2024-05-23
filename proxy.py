from abc import abstractmethod
from urllib.parse import urlparse

from flask import Flask, request, Response
import requests
import re
from CustomLogger import logger

app = Flask(__name__)
# 上游网站的域名.
upstream = 'https://theporndude.com'
# 是否禁用浏览器缓存.
disable_cache = True
# 用于替换响应文本中的内容的字典, 将"$upstream"替换为"$custom_domain".
replace_dict = {
    '$upstream': '$custom_domain',
}


def proxy_handler(
        request,
        preHeadHandlers,
        preContentHandlers,
        postHeadHandlers,
        postContentHandlers
):
    print("")





def replace_response_text(text, upstream_domain, request_domain):
    for key, value in replace_dict.items():
        search_value = key.replace('$upstream', upstream_domain).replace('$custom_domain', request_domain)
        replace_value = value.replace('$upstream', upstream_domain).replace('$custom_domain', request_domain)
        text = text.replace(search_value, replace_value)
    return text


Referer = ''
Origin = ''


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'])
def application(path):
    parsed_url = urlparse(request.url)
    request_domain = parsed_url.scheme + '://' + parsed_url.netloc
    upstream_url = request.url.replace(request_domain, upstream)

    headers = {key: value for key, value in request.headers if key.lower() != 'host'}
    headers['Host'] = upstream.split('//')[1]

    if 'Referer' in headers.keys():
        headers['Referer'] = headers['Referer'].replace(request_domain, upstream)
        global Referer
        Referer = headers['Referer']
    if 'Origin' in headers.keys():
        headers['Origin'] = headers['Origin'].replace(request_domain, upstream)
        global Origin
        Origin = headers['Origin']

    if disable_cache:
        headers['Cache-Control'] = 'no-store'

    response = requests.request(
        method=request.method,
        url=upstream_url,
        headers=headers,
        data=request.get_data(),
        cookies=request.cookies,
        allow_redirects=False
    )

    excluded_headers = ['content-encoding', 'transfer-encoding', 'content-length', 'connection']
    headers = [(name, value) for name, value in response.raw.headers.items() if name.lower() not in excluded_headers]
    headers.append(('access-control-allow-origin', '*'))
    headers.append(('access-control-allow-credentials', 'true'))

    content_type = response.headers.get('content-type', '')

    # 替换当前域名的从定向
    if response.is_redirect:
        location = response.headers.get('Location', '')
        location = location.replace(upstream, request_domain)
        response.headers['Location'] = location

    if 'text/html' in content_type and 'UTF-8' in content_type:
        content = replace_response_text(response.text, upstream, request_domain)
        return Response(content, response.status_code, headers)
    else:
        return Response(response.content, response.status_code, headers)


@app.route('/proxy/', defaults={'path': ''})
@app.route('/proxy/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'])
def proxy(path):
    parsed_url = urlparse(request.url)
    headers = {key: value for key, value in request.headers if key.lower() != 'host'}

    parsed_upstream = urlparse(path)
    headers['Host'] = parsed_upstream.netloc

    request_domain = parsed_url.scheme + '://' + parsed_url.netloc

    if 'Referer' in headers.keys():
        headers['Referer'] = headers['Referer'].replace(request_domain, upstream)
        global Referer
        Referer = headers['Referer']
    if 'Origin' in headers.keys():
        headers['Origin'] = headers['Origin'].replace(request_domain, upstream)
        global Origin
        Origin = headers['Origin']

    response = requests.request(
        method=request.method,
        url=path,
        headers=headers,
        data=request.get_data(),
        cookies=request.cookies,
        allow_redirects=False
    )
    return Response(response.content, response.status_code, headers)


def parserUrl(url):
    parsed_url = urlparse(request.url)
    return {
        "site": parsed_url.scheme + '://' + parsed_url.netloc,
        "path": parsed_url.path,
        "host": parsed_url.netloc
    }


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
