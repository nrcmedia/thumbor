FROM python:2.7

RUN apt-get update \
    && apt-get install -y \
        gifsicle

COPY . /thumbor-src/
RUN pip install /thumbor-src/ \
    && rm -rf /thumbor-src/ \
    && pip install newrelic \
        opencv-python

RUN groupadd -g 999 thumbor \
    && useradd -r -m -u 999 -g thumbor thumbor \
    && install -d -o thumbor /var/cache/thumbor

USER thumbor
CMD ["/usr/local/bin/thumbor", "-c", "/thumbor.conf", "--port", "8000"]
