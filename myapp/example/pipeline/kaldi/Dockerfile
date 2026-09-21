
# docker build --network=host -t modelone/kaldi:gpu-ubuntu18.04-cuda10.0-2023-05-08 .

FROM kaldiasr/kaldi:gpu-ubuntu18.04-cuda10.0-2023-05-08

RUN pip config set global.index-url https://mirrors.aliyun.com/pypi/simple

RUN apt update -y && apt install -y openssh-server openssh-client git vim
RUN git clone https://github.com/kaldi-asr/kaldi.git

