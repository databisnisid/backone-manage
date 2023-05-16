FROM python:3.10
#FROM nikolaik/python3.10-nodejs20-slim

# set work directory
#WORKDIR /home/pn/app
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
