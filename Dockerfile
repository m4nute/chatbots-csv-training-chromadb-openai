FROM python:3.11.5

RUN apt-get update --fix-missing && apt-get install -y --fix-missing build-essential


WORKDIR /code

COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY ./app /code/app