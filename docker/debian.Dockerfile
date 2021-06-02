FROM python:3.9-slim-buster as builder

#Global deps
RUN apt-get update && apt-get install -y binutils
RUN pip3 install --upgrade pip
RUN pip3 install --upgrade pyinstaller setuptools
RUN pip3 install cryptography

# Local deps
RUN mkdir -p /tmp/build
COPY requirements.txt /tmp/build
RUN pip3 install -r /tmp/build/requirements.txt && rm -rf /tmp/build/*

COPY . /tmp/build/
RUN cd /tmp/build && pyinstaller cli.spec && mv dist/swarm-cli /usr/bin/swarm-cli




