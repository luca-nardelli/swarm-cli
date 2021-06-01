#! /bin/sh

CURRENT_DIR=`pwd`
UID=`id -u`

IMAGE='registry.gitlab.com/sungazer-pub/swarm-cli'
docker build -t ${IMAGE}:alpine -f docker/alpine.Dockerfile .

# Export artifacts
docker run -u ${UID} --rm -v "${CURRENT_DIR}/dist:/dist" ${IMAGE}:alpine sh -c "rm -rf /dist/alpine && mkdir -p /dist/alpine && cp /usr/bin/swarm-cli /dist/alpine/swarm-cli"