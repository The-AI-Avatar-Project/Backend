FROM quay.io/keycloak/keycloak:26.2

WORKDIR /opt/keycloak
EXPOSE 8080
# REMOVE THIS LINE:
ENTRYPOINT ["./bin/kc.sh","start","--http-port=8080","--http-enabled=true"]
