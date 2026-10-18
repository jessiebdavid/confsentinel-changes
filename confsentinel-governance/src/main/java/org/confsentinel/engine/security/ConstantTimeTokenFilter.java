package org.confsentinel.engine.security;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.Ordered;
import org.springframework.core.annotation.Order;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;

@Component
@Order(Ordered.HIGHEST_PRECEDENCE + 10)
public class ConstantTimeTokenFilter extends OncePerRequestFilter {

    private final String governanceToken;
    private final String ciToken;

    public ConstantTimeTokenFilter(
            @Value("${confsentinel.security.governance-token:secret-governance-token-xyz}") String governanceToken,
            @Value("${confsentinel.security.ci-token:secret-ci-token-abc}") String ciToken
    ) {
        this.governanceToken = governanceToken;
        this.ciToken = ciToken;
    }

    @Override
    protected void doFilterInternal(
            HttpServletRequest request,
            HttpServletResponse response,
            FilterChain filterChain
    ) throws ServletException, IOException {

        String path = request.getRequestURI();
        String method = request.getMethod();

        // 1. Allow Actuator and CORS Preflight requests
        if ("OPTIONS".equalsIgnoreCase(method) || path.startsWith("/actuator")) {
            filterChain.doFilter(request, response);
            return;
        }

        // 2. Protect Rule Ingestion (POST /api/v1/rules) with Governance Token
        if (path.startsWith("/api/v1/rules") && "POST".equalsIgnoreCase(method)) {
            String token = extractToken(request, "X-Governance-Token");
            if (!isTokenValid(token, this.governanceToken)) {
                sendUnauthorized(response, "Invalid or missing X-Governance-Token header");
                return;
            }
        }

        // 3. Protect CI Telemetry Ingestion (POST /api/v1/evaluations) with CI Token
        if (path.startsWith("/api/v1/evaluations") && "POST".equalsIgnoreCase(method)) {
            String token = extractToken(request, "X-CI-Token");
            if (!isTokenValid(token, this.ciToken)) {
                sendUnauthorized(response, "Invalid or missing X-CI-Token header");
                return;
            }
        }

        // 4. Pass read-only queries (Dashboard / Reports / Active Rules)
        filterChain.doFilter(request, response);
    }

    private String extractToken(HttpServletRequest request, String headerName) {
        String token = request.getHeader(headerName);
        if (token == null || token.isBlank()) {
            String authHeader = request.getHeader("Authorization");
            if (authHeader != null && authHeader.startsWith("Bearer ")) {
                token = authHeader.substring(7).trim();
            }
        }
        return token;
    }

    private boolean isTokenValid(String provided, String expected) {
        if (provided == null || expected == null) {
            return false;
        }
        byte[] providedBytes = provided.getBytes(StandardCharsets.UTF_8);
        byte[] expectedBytes = expected.getBytes(StandardCharsets.UTF_8);
        return MessageDigest.isEqual(providedBytes, expectedBytes);
    }

    private void sendUnauthorized(HttpServletResponse response, String message) throws IOException {
        response.setStatus(HttpServletResponse.SC_UNAUTHORIZED);
        response.setContentType("application/json");
        response.getWriter().write(String.format("{\"error\": \"UNAUTHORIZED\", \"message\": \"%s\"}", message));
    }
}