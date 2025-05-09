FROM --platform=linux/amd64 maven:3.9.9 AS builder
WORKDIR /usr/src/myapp
COPY pom.xml .
RUN mvn dependency:go-offline
COPY ./src/ ./src
RUN mvn clean package

FROM --platform=linux/amd64 eclipse-temurin:21-jre-alpine
WORKDIR /usr/src/myapp
COPY --from=builder /usr/src/myapp/target/backend-0.0.1-SNAPSHOT.jar app.jar
CMD ["java", "-jar", "app.jar"]
