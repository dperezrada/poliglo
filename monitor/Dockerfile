FROM node:6.9

ADD package.json bower.json /src/monitor/
WORKDIR /src/monitor
RUN npm install -d && npm run bower:install -- --allow-root

EXPOSE 9000
CMD ["npm", "run", "serve"]