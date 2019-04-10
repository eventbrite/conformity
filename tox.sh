#!/bin/bash -ex

docker build -t conformity-test .

if [[ -z "$1" ]]
then
    docker run -it --rm conformity-test
else
    docker run -it --rm conformity-test tox "$@"
fi
