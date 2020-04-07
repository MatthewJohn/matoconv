FROM node:10-buster-slim
# Adds backports
# Installs git, unoconv and chinese fonts

RUN mkdir -p /usr/share/man/man1
RUN apt-get update && apt-get -y install \
    git \
    unoconv \
    ttf-wqy-zenhei \
    fonts-arphic-ukai \
    fonts-arphic-uming \
    fonts-indic \
    python3 \
    python3-flask \
    libreoffice \
    python3-flask-cors \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir /app
WORKDIR /app
ADD . /app/

ENTRYPOINT python3 -u /app/server.py
