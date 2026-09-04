FROM fnproject/python:3.12-dev AS build-stage

WORKDIR /function
ENV PYTHONPATH=/python

COPY requirements.txt /function/
RUN pip3 install --target /python --no-cache --no-cache-dir -r requirements.txt && \
    rm -fr ~/.cache/pip /tmp* /function/requirements.txt

COPY func.py func.yaml /function/

FROM fnproject/python:3.12

WORKDIR /function
COPY --from=build-stage /python /python
COPY --from=build-stage /function /function

ENV PYTHONPATH=/python
ENTRYPOINT ["/python/bin/fdk", "/function/func.py", "handler"]
