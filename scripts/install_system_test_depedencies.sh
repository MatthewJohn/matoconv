#!/bin/bash

set -e
set -x

pip3 install -r ./requirements.system-tests.txt
apt-get update && apt-get install --assume-yes imagemagick poppler-utils firefox-esr && apt-get clean all
sed -i 's/.*"PDF".*//g' /etc/ImageMagick-6/policy.xml


