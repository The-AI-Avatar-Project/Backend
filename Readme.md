# KI-Avatar Backend

## Requirements
The only requirement is [Docker](https://www.docker.com/). If you want to make changes to the Java code, it is recommended to also install [Java 21](https://adoptium.net/de/temurin/releases/) and [Maven](https://maven.apache.org/download.cgi). To talk to the openai backend, an openai key is needed. This should be placed in the `.env`. You can use `example.env` as an example.

## Starting
To start the backend, simply run `docker compose up --build`. 

## Accessing

### Adminer
After following the steps in [Starting](#Starting), adminer is accessible on `http://localhost:8081`. To access the data, set the System to `PostgreSQL`, the server to `db`, the user to `postgres` and the password to `example`. After the login, click on the aiAvatar database to see the tables and data.

### Backend
The backend is accessible on `http://localhost:8080`. Swagger UI is available on `http://localhost:8080/swagger-ui/index.html`