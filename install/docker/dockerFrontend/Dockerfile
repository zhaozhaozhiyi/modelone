# docker build -t modelone/kubeflow-dashboard-frontend:2026.06.01 -f install/docker/dockerFrontend/Dockerfile .

ARG MODELONE_NGINX_IMAGE=nginx:stable
FROM ${MODELONE_NGINX_IMAGE}

LABEL org.opencontainers.image.title="modelOne frontend"

# 环境变量
ENV TZ=Asia/Shanghai \
    RUN_USER=nginx \
    RUN_GROUP=nginx \
    DATA_DIR=/data/web \
    LOG_DIR=/data/log/nginx

# 工作目录
WORKDIR ${DATA_DIR}

# 切换为上海时区
RUN ln -sf /usr/share/zoneinfo/$TZ /etc/localtime \
    && echo $TZ > /etc/timezone

# 创建日志文件夹
RUN mkdir ${LOG_DIR} -p
RUN chown nginx.nginx -R ${LOG_DIR}

RUN rm -rf ./frontend ./static && mkdir ./frontend ./static

# 拷贝dist包文件
COPY ./myapp/static/appbuilder/frontend ./frontend
COPY ./myapp/static ./static
COPY LICENSE /usr/share/licenses/modelone/LICENSE
# PWA metadata is part of the product build and must be delivered.

RUN find frontend -name ".DS_Store" -type f -delete
RUN find static -name ".DS_Store" -type f -delete

RUN chmod -R 777 frontend
RUN chmod -R 777 static
# 拷贝nginx配置文件
ADD install/docker/dockerFrontend/nginx.conf /etc/nginx/nginx.conf
ADD install/docker/dockerFrontend/nginx.80.conf /etc/nginx/conf.d/default.conf
ENTRYPOINT []
CMD ["nginx", "-g", "daemon off;"]
