FROM python:3.8-slim-buster
WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY . .

CMD python3 main.py
# +++ Made By Obito [telegram username: @i_killed_my_clan] +++ #
