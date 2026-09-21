# docker build -t modelone/kubeflow-dashboard:2026.06.01 -f install/docker/Dockerfile .

ARG MODELONE_IMAGE_PREFIX
ARG MODELONE_BACKEND_BASE_IMAGE=${MODELONE_IMAGE_PREFIX}modelone/kubeflow-dashboard:base-python3.9-20260501
FROM ${MODELONE_BACKEND_BASE_IMAGE}

RUN mkdir -p /cube-studio/aihub

# Reused base images must not retain deleted public brand assets.
RUN rm -rf /home/myapp/myapp/static /data/web/frontend

COPY config/modelone.json /home/myapp/config/modelone.json
COPY LICENSE /usr/share/licenses/modelone/LICENSE
COPY myapp /home/myapp/myapp
COPY install/docker/config.py /home/myapp/myapp/config.py
COPY install/docker/project.py /home/myapp/myapp/project.py
COPY myapp/static/appbuilder/frontend /data/web/frontend
COPY aihub /cube-studio/aihub
COPY job-template /cube-studio/job-template
ENV PATH=/home/myapp/myapp/bin:${PATH:-}
ENV PYTHONPATH=/home/myapp:${PYTHONPATH:-}
COPY install/docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /home/myapp/myapp/bin/myapp /entrypoint.sh

# ENTRYPOINT ["bash","/entrypoint.sh"]

# HEALTHCHECK CMD ["curl", "-f", "http://localhost:80/health"]
