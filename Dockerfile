# 使用更小的基础镜像
FROM python:3.12.3-slim
# 维护者信息
LABEL maintainer="TimeHo"
# 设置工作目录并复制内容
WORKDIR /Gproxy
COPY . /Gproxy
# 使用无缓存模式安装依赖，减少镜像体积
RUN pip install --no-cache-dir -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/
# 暴露应用端口
EXPOSE 5000
# 设置容器启动时运行的命令
CMD ["gunicorn", "-c", "gunicorn_config.py", "app:app"]
