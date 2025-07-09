FROM ubuntu:22.04

RUN apt-get update && \
    apt-get install -y \
        git \
        pkg-config \
        software-properties-common \
        wget
RUN add-apt-repository ppa:deadsnakes/ppa && \
    apt-get update && \
    apt-get install -y \
        python3.7 \
        python3.7-dev \
        python3.8 \
        python3.8-distutils \
        python3.8-dev \
        python3.12 \
        python3.12-dev
RUN wget https://bootstrap.pypa.io/get-pip.py -O /tmp/get-pip.py && \
    python3.12 /tmp/get-pip.py && \
    python3.12 -m pip install tox

WORKDIR /test/conformity

CMD ["tox"]

ADD . /test/conformity
