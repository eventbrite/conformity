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
        python2.7 \
        python2.7-dev \
        python3.4 \
        python3.4-dev \
        python3.5 \
        python3.5-dev \
        python3.6 \
        python3.6-dev \
        python3.7 \
        python3.7-dev \
        python3.8 \
        python3.8-distutils \
        python3.8-dev \
        python3.9 \
        python3.9-distutils \
        python3.9-dev \
        python3.10 \
        python3.10-distutils \
        python3.10-dev \
        python3.11 \
        python3.11-distutils \
        python3.11-dev \
        python3.12 \
        python3.12-distutils \
        python3.12-dev
RUN wget https://bootstrap.pypa.io/get-pip.py -O /tmp/get-pip.py && \
    python3.12 /tmp/get-pip.py && \
    python3.12 -m pip install tox

WORKDIR /test/conformity

CMD ["tox"]

ADD . /test/conformity
