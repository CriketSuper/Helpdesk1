FROM python:3.9

RUN apt-get update && \
    apt-get install -y postgresql && \
    apt-get clean

RUN mkdir /app
WORKDIR /app

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app/

RUN python helpdesk/manage.py migrate

EXPOSE 1234

CMD ["python", "helpdesk/manage.py", "runserver", "0.0.0.0:1234"]
