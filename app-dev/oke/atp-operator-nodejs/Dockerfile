FROM node:16.16.0

WORKDIR /

RUN apt-get update && apt-get install -y libaio1

ENV LD_LIBRARY_PATH=/instantclient_21_7

COPY ["package.json", "package-lock.json*", "./"]

RUN npm install

COPY . .

RUN unzip instantclient-basic-linux.x64-21.7.0.0.0dbru.zip

RUN rm -f instantclient-basic-linux.x64-21.7.0.0.0dbru.zip

CMD [ "node", "server.js" ]
