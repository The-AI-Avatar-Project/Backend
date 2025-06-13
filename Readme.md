# KI-Avatar Backend

## Requirements
The only requirement is [Docker](https://www.docker.com/). If you want to make changes to the Java code, it is recommended to also install [Java 21](https://adoptium.net/de/temurin/releases/) and [Maven](https://maven.apache.org/download.cgi). To talk to the openai backend, an openai key is needed. This should be placed in the `.env`. You can use `example.env` as an example.

## Prerequisites
Follow the readme in `services/wav2lip/README.md`

## Starting
To start the backend, simply run `docker compose up --build`. 

## Post start
After the backend has started successfully, you need to grab the keycloak backend-client token and paste it into `src/main/resources/application.properties`. To grab the token:
1. go to [the Keycloak interface](http://localhost:8084/admin/master/console/#/AI-Avatar/clients/). Username: `admin` Passwort: `secret`
2. Click on the backend-client -> Credentials
3. Copy the client secret
4. Paste into the `keycloak.admin-token` field of `src/main/resources/application.properties`

## Accessing

### Adminer
After following the steps in [Starting](#Starting), adminer is accessible on `http://localhost:8081`. To access the data, set the System to `PostgreSQL`, the server to `db`, the user to `postgres` and the password to `example`. After the login, click on the aiAvatar database to see the tables and data.

### Backend
The backend is accessible on `http://localhost:8080`. Swagger UI is available on `http://localhost:8080/swagger-ui/index.html`