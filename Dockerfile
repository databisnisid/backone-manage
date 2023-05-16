#FROM python:3.10
#FROM nikolaik/python3.10-nodejs20-slim
FROM ubuntu:22.04
RUN apt-get update && apt-get install -y locales && rm -rf /var/lib/apt/lists/* \
 && localedef -i en_US -c -f UTF-8 -A /usr/share/locale/locale.alias en_US.UTF-8
ENV LANG en_US.utf8

RUN rm -fr /etc/localtime
RUN ln -s /usr/share/zoneinfo/Asia/Jakarta /etc/localtime

RUN apt-get update && apt-get install -y \
 locales \
 python3-pip \
 libgdal1-dev \
 libxft-dev \
 libfreetype6-dev \
 libffi-dev \
 vim \
 nodejs \
 npm \
 curl \
 wget

RUN mkdir /app
WORKDIR /app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

#RUN apt update
# install dependencies
RUN pip install --upgrade pip
COPY requirements.txt /app
RUN pip install -r requirements.txt

# copy project
COPY . /app

EXPOSE 8008

#CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
ENTRYPOINT ["./entrypoint.ds"]
