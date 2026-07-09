FROM node:16.16.0

WORKDIR /

RUN apt-get update && apt-get install -y libaio1

ENV LD_LIBRARY_PATH=/instantclient_23_3

COPY ["package.json", "package-lock.json*", "./"]

RUN npm install

COPY . .

RUN unzip instantclient-basic-linux.x64-23.3.0.0.0.zip

RUN rm -f instantclient-basic-linux.x64-23.3.0.0.0.zip

CMD [ "node", "server.js" ]
