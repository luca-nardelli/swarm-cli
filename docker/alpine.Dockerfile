FROM python:3.9-alpine as builder

#Global deps
RUN apk add --update --no-cache build-base libffi-dev openssl openssl-dev rust cargo
RUN pip3 install --upgrade pip
RUN pip3 install --upgrade pyinstaller setuptools
RUN pip3 install cryptography

# Local deps
RUN mkdir -p /tmp/build
COPY requirements.txt /tmp/build
RUN pip3 install -r /tmp/build/requirements.txt && rm -rf /tmp/build/*

COPY swarm_cli cli.py cli.spec /tmp/build/
RUN cd /tmp/build && pyinstaller cli.spec && mv dist/swarm-cli /usr/bin/swarm-cli




