ARG MODELONE_IMAGE_PREFIX
FROM ${MODELONE_IMAGE_PREFIX}modelone/notebook:jupyter-ubuntu22.04

RUN apt-get update && apt install -y lsof

COPY machinelearning/modelone-examples/ /examples/

# 爬虫包
RUN pip install pyquery requests lxml beautifulsoup4 \
    && rm -rf /tmp/* /var/tmp/* /root/.cache

# 数据库查询包
RUN pip install pymysql pika presto-python-client neo4j elasticsearch psycopg2-binary sqlalchemy torndb kafka paramiko prometheus_client oss2 happybase clickhouse-sqlalchemy clickhouse-driver pymongo presto-python-client \
    && rm -rf /tmp/* /var/tmp/* /root/.cache

# 数据挖掘包
RUN pip install numpy pandas sklearn wheel SciPy pyarrow Pillow PyML MDP Theano opencv-python plotly tqdm gbdt xgboost lightgbm \
    && rm -rf /tmp/* /var/tmp/* /root/.cache

# 可视化包
RUN pip install matplotlib pyecharts \
    && rm -rf /tmp/* /var/tmp/* /root/.cache

# 数据服务包
RUN pip install gevent flask asyncio uvloop aiohttp grpcio protobuf grpcio-tools pysnooper \
    && rm -rf /tmp/* /var/tmp/* /root/.cache

# 拷贝examples
COPY machinelearning/examples/* /examples/

# 环境初始化配置
COPY machinelearning/init.sh /init.sh
COPY notebook_init.py /opt/modelone/notebook_init.py
RUN rm -f /etc/ssh/ssh_host_*
RUN python3 -m ipykernel install --sys-prefix --name modelone --display-name "modelOne Python"
