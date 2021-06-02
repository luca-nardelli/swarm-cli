#! /bin/sh

TAG=${TAG:-"latest"}

git tag -f $TAG
git push && git push --tags -f
gh release delete $TAG
gh release create $TAG -n '' -t 'Dev build' -p ./dist/*