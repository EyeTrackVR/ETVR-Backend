#!/bin/sh

# This script is used to setup the environment for the build process.

# check if make is installed and if not install it
if ! command -v make &> /dev/null
then
    echo "make could not be found, installing it now"
    apt-get install make
fi

# check if poetry is installed and if not install it

if ! command -v poetry &> /dev/null
then
    echo "poetry could not be found, installing it now"
    apt-get install poetry
fi

