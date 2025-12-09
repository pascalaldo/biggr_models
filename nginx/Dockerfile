FROM nginx:1.19.0-alpine
ARG BIGGR_SERVER_TYPE=prod

COPY ./default-$BIGGR_SERVER_TYPE.conf /etc/nginx/conf.d/default.conf
RUN [ "$BIGGR_SERVER_TYPE" == "prod" ] && mkdir -p /etc/nginx/ssl/live/biggr.org || echo "Not in production"
