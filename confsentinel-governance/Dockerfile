# ==========================================
# Stage 1: Build Environment
# ==========================================
FROM eclipse-temurin:21-jdk-alpine AS builder

WORKDIR /workspace

# Install curl for health checks if needed and layer cache Maven wrapper / POM
RUN apk add --no-cache bash

COPY pom.xml .
COPY .mvn .mvn
COPY mvnw .

# Download dependencies offline for fast Docker layer caching
RUN chmod +x ./mvnw && ./mvnw dependency:go-offline -B

# Copy application source code
COPY src src

# Build and package the production executable JAR (skipping tests here as CI executes them prior)
RUN ./mvnw clean package -DskipTests -B

# Extract jar layers for Spring Boot layer index caching
RUN java -Djarmode=layertools -jar target/*.jar extract --destination target/extracted

# ==========================================
# Stage 2: Minimal Secure Runtime
# ==========================================
FROM eclipse-temurin:21-jre-alpine AS runtime

LABEL org.opencontainers.image.title="ConfSentinel Governance Engine" \
      org.opencontainers.image.description="Central Policy Governance and Compliance Ingestion Engine" \
      org.opencontainers.image.licenses="Apache-2.0"

# Install curl/wget for container health checking
RUN apk add --no-cache wget curl tzdata

# Create dedicated unprivileged system user and group
RUN addgroup -S confsentinel && adduser -S confsentinel -G confsentinel

WORKDIR /app

# Copy layered Spring Boot artifacts from builder
COPY --from=builder --chown=confsentinel:confsentinel /workspace/target/extracted/dependencies/ ./
COPY --from=builder --chown=confsentinel:confsentinel /workspace/target/extracted/spring-boot-loader/ ./
COPY --from=builder --chown=confsentinel:confsentinel /workspace/target/extracted/snapshot-dependencies/ ./
COPY --from=builder --chown=confsentinel:confsentinel /workspace/target/extracted/application/ ./

# Switch to non-root user
USER confsentinel:confsentinel

# Expose HTTP API Port
# Interfaces exposed:
# - CLI Ingress: /api/v1/rules, /api/v1/evaluations
# - UI Ingress:  /api/v1/reports/summary, /api/v1/reports/drift/{serviceId}
# - Ops/Health:  /actuator/health, /actuator/metrics
EXPOSE 8080

# Health Check contract via Spring Boot Actuator
HEALTHCHECK --interval=15s --timeout=3s --start-period=20s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:8080/actuator/health || exit 1

# Container-aware JVM memory configuration
ENTRYPOINT ["java", \
  "-XX:+UseContainerSupport", \
  "-XX:MaxRAMPercentage=75.0", \
  "-XX:InitialRAMPercentage=50.0", \
  "-Djava.security.egd=file:/dev/./urandom", \
  "org.springframework.boot.loader.launch.JarLauncher"]