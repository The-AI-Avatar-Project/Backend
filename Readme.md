# KI-Avatar Backend

## Requirements
The only requirement is [Docker](https://www.docker.com/). If you want to make changes to the Java code, it is recommended to also install [Java 21](https://adoptium.net/de/temurin/releases/) and [Maven](https://maven.apache.org/download.cgi). To talk to the openai backend, an openai key is needed. This should be placed in the `./models/openai/.env`. You can use `example.env` as an example.

## Starting
There are two ways to start the backend. You can run it inside docker compose together with the db and the models [Prod](#Prod), or you can run it outside the container [Dev](#Dev)

### Prod
Simply run `docker compose -f compose.prod.yaml -f compose.yaml up` to start the backend. Remember to run `docker compose -f compose.prod.yaml -f compose.yaml up --build` each time the code changes.

### Dev
First run `docker compose up` to start the db and adminer. Then run `mvn clean verify spring-boot:run` to compile and start the backend.

## Accessing

### Adminer
After following the steps in [Starting](#Starting), adminer is accessible on `http://localhost:8081`. To access the data, set the System to `PostgreSQL`, the server to `db`, the user to `postgres` and the password to `example`. After the login, click on the aiAvatar database to see the tables and data.

### Backend
The backend is accessible on `http://localhost:8080`. Swagger UI is available on `http://localhost:8080/swagger-ui/index.html`