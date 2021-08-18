FROM node:10-buster-slim

RUN mkdir -p /usr/share/man/man1
RUN apt-get update && apt-get -y install \
    git \
    unoconv \
    ttf-wqy-zenhei \
    fonts-arphic-ukai \
    fonts-arphic-uming \
    fonts-indic \
    python3 \
    python3-pip \
    libreoffice \
    && rm -rf /var/lib/apt/lists/*

RUN apt-get update && apt-get -y install pdftohtml \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir /app
WORKDIR /app

COPY requirements.txt .
RUN pip3 install -r requirements.txt

ADD . /app/

ENV LISTEN_PORT 8091

ENTRYPOINT python3 -u /app/server.py
