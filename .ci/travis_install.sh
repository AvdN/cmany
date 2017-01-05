#!/bin/bash

# https://docs.travis-ci.com/user/multi-os/

set -e
set -x

if [ $TRAVIS_OS_NAME == 'linux' ] ; then

    sudo apt-get update
    sudo apt-get install -y python3-pip python3-dev
    sudo apt-get install -y cmake build-essential

    PYTHON=python3
    PIP=pip3

elif [ $TRAVIS_OS_NAME == 'osx' ] ; then

    brew update
    #brew install cmake

    brew install pyenv
    eval "$(pyenv init -)"
    v="${PY}.0"
    pyenv install $v
    pyenv global $v

    PYTHON=python$PY
    PIP=pip$PY

fi

cmake --version
cmake --help
which cc && cc --version
which c++ && c++ --version
which g++ && (g++ -dumpversion ; g++ --version)
which clang++ && (clang++ -dumpversion ; clang++ --version)

which $PYTHON
which $PIP
$PYTHON -V
$PIP -V
$PIP install -r requirements_test.txt .

exit 0
