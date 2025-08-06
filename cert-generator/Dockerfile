FROM alpine:latest

RUN apk add --no-cache openssl

WORKDIR /certs

CMD ["sh", "-c", "\
  openssl req -x509 -nodes -days 365 \
    -newkey rsa:2048 \
    -keyout key.pem \
    -out cert.pem \
    -subj \"/CN=${DOMAIN:-localhost}\" && \
  chmod 644 key.pem cert.pem"]
