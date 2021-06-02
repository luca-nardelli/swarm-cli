#! /bin/sh

CURRENT_DIR=`pwd`
UID=`id -u`
VARIANTS="alpine debian"

IMAGE='registry.gitlab.com/sungazer-pub/swarm-cli'
for v in $VARIANTS
do
  docker build -t ${IMAGE}:${v} -f docker/${v}.Dockerfile .
done


# Export artifacts
rm -rf dist/*

for v in $VARIANTS
do
  docker run -u ${UID} --rm -v "${CURRENT_DIR}/dist:/dist" ${IMAGE}:${v} sh -c "cp /usr/bin/swarm-cli /dist/swarm-cli.${v}"
done
