FROM python:3.10
ENV PYTHONUNBUFFERED=1
RUN mkdir /app
WORKDIR /app

# Install dependencies

# RUN wget https://github.com/draeger-lab/ModelPolisher/releases/download/1.7/ModelPolisher-1.7.jar

#RUN apt-get update && apt-get install -y \
#  libxml2-dev postgresql-client openjdk-17-jre
RUN apt-get update && apt-get install -y \
  libxml2-dev postgresql-client

COPY requirements.txt /app/
RUN pip install -r requirements.txt

RUN git clone https://github.com/pascalaldo/bigg_models_data.git bigg_models_data

RUN git clone -b optimizations https://github.com/pascalaldo/cobradb.git cobradb
WORKDIR /app/cobradb
RUN python setup.py install
WORKDIR /app

COPY bigg_models/ /app/bigg_models/
COPY bin/ /app/bin/
COPY scripts/ /app/scripts/
COPY pytest.ini /app/
COPY setup.cfg /app/
COPY setup.py /app/

COPY settings.ini /app/settings.ini

RUN python setup.py install

RUN rm -rf bigg_models
#CMD ["python", "-m", "bigg_models.server", "--port=8910", "--processes=6"]
CMD ["bin/server-entrypoint.sh"]
