FROM maven:3.9-eclipse-temurin-17 as builder
WORKDIR /app
COPY pom.xml .
RUN mvn dependency:resolve -DskipTests
COPY src/ ./src/
RUN mvn clean package -DskipTests -q
FROM eclipse-temurin:17-jre-alpine
WORKDIR /app
COPY --from=builder /app/target/astrobot-backend-*.jar app.jar
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD wget --quiet --tries=1 --spider http://localhost:8080/actuator/health || exit 1
ENV JAVA_OPTS="-Dfile.encoding=UTF-8 -Duser.timezone=UTC"
ENV PYTHON_API_URL=http://astrobot-api:8000
ENTRYPOINT ["java", "-XX:+UseG1GC", "-XX:MaxRAMPercentage=75.0", "-jar", "app.jar"]