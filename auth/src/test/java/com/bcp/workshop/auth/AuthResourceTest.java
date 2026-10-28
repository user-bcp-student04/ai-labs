package com.bcp.workshop.auth;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import jakarta.inject.Inject;
import io.quarkus.test.junit.QuarkusMock;
import io.quarkus.test.junit.QuarkusTest;
import org.junit.jupiter.api.Test;

import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.PreparedStatement;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.Base64;
import java.util.UUID;

import static io.restassured.RestAssured.given;
import static org.hamcrest.CoreMatchers.is;
import static org.hamcrest.Matchers.notNullValue;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

@QuarkusTest
class AuthResourceTest {
    @Inject
    LegacyDatabase database;

    @Inject
    PasswordHasher passwordHasher;

    @Test
    void reportsHealthWithoutConfiguredChecks() {
        given()
                .accept("application/json")
                .when().get("/q/health")
                .then()
                .statusCode(200)
                .body("status", is("UP"))
                .body("checks.size()", is(0));
    }

    @Test
    void logsInWithWorkshopUser() {
        given()
                .contentType("application/json")
                .body("{\"username\":\"student\",\"password\":\"Workshop123!\",\"client\":\"angular-workshop\"}")
                .when().post("/auth/login")
                .then()
                .statusCode(200)
                .body("user.username", is("student"))
                .body("user.displayName", is("Workshop Student"))
                .body("token", notNullValue())
                .body("expiresIn", is(3600))
                .body("user.role", is("STUDENT"))
                .body("debug", is("authenticated-with-legacy-flow"));
    }

    @Test
    void rejectsInvalidCredentials() {
        given()
                .contentType("application/json")
                .body("{\"username\":\"student\",\"password\":\"incorrect-password\"}")
                .when().post("/auth/login")
                .then()
                .statusCode(401)
                .body("message", is("Invalid user student or password"));
    }

    @Test
    void preservesValidationResponsesForMissingLoginFields() {
        given()
                .contentType("application/json")
                .body("null")
                .when().post("/auth/login")
                .then()
                .statusCode(400)
                .body("message", is("Request is null"));

        given()
                .contentType("application/json")
                .body("{\"username\":\"\",\"password\":\"password\"}")
                .when().post("/auth/login")
                .then()
                .statusCode(400)
                .body("message", is("Username is required"));

        given()
                .contentType("application/json")
                .body("{\"username\":\"student\",\"password\":\"\"}")
                .when().post("/auth/login")
                .then()
                .statusCode(400)
                .body("message", is("Password is required"));
    }

    @Test
    void rejectsWhitespaceOnlyLoginFields() {
        given()
                .contentType("application/json")
                .body("{\"username\":\"   \",\"password\":\"password\"}")
                .when().post("/auth/login")
                .then()
                .statusCode(400)
                .body("message", is("Username is required"));

        given()
                .contentType("application/json")
                .body("{\"username\":\"student\",\"password\":\"   \"}")
                .when().post("/auth/login")
                .then()
                .statusCode(400)
                .body("message", is("Password is required"));
    }

    @Test
    void rejectsMalformedJsonWithEmptyBadRequestBody() {
        given()
                .contentType("application/json")
                .body("{bad json")
                .when().post("/auth/login")
                .then()
                .statusCode(400)
                .body(is(""));
    }

    @Test
    void rejectsUnsupportedRequestContentTypeWithEmptyBody() {
        given()
                .contentType("text/plain")
                .body("{\"username\":\"student\",\"password\":\"Workshop123!\"}")
                .when().post("/auth/login")
                .then()
                .statusCode(415)
                .body(is(""));
    }

    @Test
    void rejectsUnsupportedResponseMediaTypeWithEmptyBody() {
        given()
                .accept("text/plain")
                .contentType("application/json")
                .body("{\"username\":\"student\",\"password\":\"Workshop123!\"}")
                .when().post("/auth/login")
                .then()
                .statusCode(406)
                .body(is(""));
    }

    @Test
    void rejectsCredentialsContainingQuoteWhenTheyDoNotMatch() {
        given()
                .contentType("application/json")
                .body("{\"username\":\"student\",\"password\":\"incorrect'password\"}")
                .when().post("/auth/login")
                .then()
                .statusCode(401);
    }

    @Test
    void returnsSignedTokenWithExplicitClaims() throws Exception {
        String token = given()
                .contentType("application/json")
                .body("{\"username\":\"student\",\"password\":\"Workshop123!\"}")
                .when().post("/auth/login")
                .then()
                .statusCode(200)
                .extract()
                .path("token");

        String[] tokenParts = token.split("\\.");
        assertEquals(3, tokenParts.length);

        ObjectMapper objectMapper = new ObjectMapper();
        JsonNode header = objectMapper.readTree(Base64.getUrlDecoder().decode(tokenParts[0]));
        JsonNode claims = objectMapper.readTree(Base64.getUrlDecoder().decode(tokenParts[1]));
        assertEquals("HS256", header.path("alg").asText());
        assertEquals("JWT", header.path("typ").asText());
        assertEquals("student", claims.path("sub").asText());
        assertEquals("STUDENT", claims.path("role").asText());

        long expiry = claims.path("exp").asLong();
        long now = Instant.now().getEpochSecond();
        assertTrue(expiry > now);
        assertTrue(expiry <= now + TokenService.EXPIRATION_SECONDS);

        Mac mac = Mac.getInstance("HmacSHA256");
        mac.init(new SecretKeySpec(
                "test-only-auth-signing-key-do-not-use".getBytes(StandardCharsets.UTF_8),
                "HmacSHA256"));
        byte[] expectedSignature = mac.doFinal(
                (tokenParts[0] + "." + tokenParts[1]).getBytes(StandardCharsets.US_ASCII));
        assertEquals(
                Base64.getUrlEncoder().withoutPadding().encodeToString(expectedSignature),
                tokenParts[2]);
    }

    @Test
    void rejectsShortTokenSigningSecrets() {
        TokenService tokenService = new TokenService();
        tokenService.secret = "short-test-key";

        assertThrows(IllegalStateException.class, tokenService::validateSecret);
    }

    @Test
    void preservesLoginForExistingPlaintextCredentials() throws Exception {
        String username = "legacy-user-" + UUID.randomUUID();
        String password = "legacy-password";
        String dbUrl = System.getenv().getOrDefault("AUTH_DB_URL", "jdbc:sqlite:./data/workshop.db");

        try (Connection connection = DriverManager.getConnection(dbUrl);
             PreparedStatement insertUser = connection.prepareStatement(
                     "INSERT INTO legacy_users(username,password,display_name,role) VALUES (?,?,?,?)")) {
            insertUser.setString(1, username);
            insertUser.setString(2, password);
            insertUser.setString(3, "Legacy Test User");
            insertUser.setString(4, "STUDENT");
            insertUser.executeUpdate();
        }

        try {
            database.initialize();

            given()
                    .contentType("application/json")
                    .body("{\"username\":\"" + username + "\",\"password\":\"" + password + "\"}")
                    .when().post("/auth/login")
                    .then()
                    .statusCode(200)
                    .body("user.username", is(username));

            String storedHash;
            try (Connection connection = DriverManager.getConnection(dbUrl);
                 PreparedStatement findPassword = connection.prepareStatement(
                         "SELECT password FROM legacy_users WHERE username=?")) {
                findPassword.setString(1, username);
                try (var storedPassword = findPassword.executeQuery()) {
                    storedPassword.next();
                    storedHash = storedPassword.getString("password");
                    assertTrue(passwordHasher.isHashed(storedHash));
                    assertTrue(passwordHasher.matches(password, storedHash));
                    assertFalse(passwordHasher.matches("wrong-password", storedHash));
                }
            }

            database.initialize();
            try (Connection connection = DriverManager.getConnection(dbUrl);
                 PreparedStatement findPassword = connection.prepareStatement(
                         "SELECT password FROM legacy_users WHERE username=?")) {
                findPassword.setString(1, username);
                try (var migratedPassword = findPassword.executeQuery()) {
                    migratedPassword.next();
                    assertEquals(storedHash, migratedPassword.getString("password"));
                }
            }
        } finally {
            try (Connection connection = DriverManager.getConnection(dbUrl);
                 PreparedStatement deleteUser = connection.prepareStatement(
                         "DELETE FROM legacy_users WHERE username=?")) {
                deleteUser.setString(1, username);
                deleteUser.executeUpdate();
            }
        }
    }

    @Test
    void migratesLegacyPlaintextPasswordThatLooksLikeHash() throws Exception {
        String username = "legacy-hash-shaped-" + UUID.randomUUID();
        String password = "$pbkdf2-sha256$210000$"
                + Base64.getEncoder().encodeToString(new byte[16]) + "$"
                + Base64.getEncoder().encodeToString(new byte[32]);
        String dbUrl = System.getenv().getOrDefault("AUTH_DB_URL", "jdbc:sqlite:./data/workshop.db");

        try (Connection connection = DriverManager.getConnection(dbUrl);
             PreparedStatement insertUser = connection.prepareStatement(
                     "INSERT INTO legacy_users(username,password,display_name,role) VALUES (?,?,?,?)")) {
            insertUser.setString(1, username);
            insertUser.setString(2, password);
            insertUser.setString(3, "Legacy Hash-Shaped User");
            insertUser.setString(4, "STUDENT");
            insertUser.executeUpdate();
        }

        try {
            database.initialize();

            given()
                    .contentType("application/json")
                    .body("{\"username\":\"" + username + "\",\"password\":\"" + password + "\"}")
                    .when().post("/auth/login")
                    .then()
                    .statusCode(200)
                    .body("user.username", is(username));

            try (Connection connection = DriverManager.getConnection(dbUrl);
                 PreparedStatement findPassword = connection.prepareStatement(
                         "SELECT password FROM legacy_users WHERE username=?")) {
                findPassword.setString(1, username);
                try (var storedPassword = findPassword.executeQuery()) {
                    storedPassword.next();
                    String storedHash = storedPassword.getString("password");
                    assertFalse(storedHash.equals(password));
                    assertTrue(passwordHasher.matches(password, storedHash));
                }
            }
        } finally {
            try (Connection connection = DriverManager.getConnection(dbUrl);
                 PreparedStatement deleteUser = connection.prepareStatement(
                         "DELETE FROM legacy_users WHERE username=?")) {
                deleteUser.setString(1, username);
                deleteUser.executeUpdate();
            }
        }
    }

    @Test
    void returnsGenericErrorWhenAuthenticationFails() {
        LegacyDatabase failingDatabase = new LegacyDatabase() {
            @Override
            void initialize() {}

            @Override
            public UserRecord findByCredentials(String username, String password) {
                throw new IllegalStateException("synthetic-database-failure");
            }
        };
        QuarkusMock.installMockForType(failingDatabase, LegacyDatabase.class);

        given()
                .contentType("application/json")
                .body("{\"username\":\"student\",\"password\":\"Workshop123!\"}")
                .when().post("/auth/login")
                .then()
                .statusCode(500)
                .body("message", is("Authentication service error"))
                .body("exception", is("InternalServerError"));
    }

    @Test
    void passwordHashesUseUniqueSaltsAndRejectMalformedValues() {
        String firstHash = passwordHasher.hash("isolated-test-password");
        String secondHash = passwordHasher.hash("isolated-test-password");

        assertTrue(passwordHasher.isHashed(firstHash));
        assertTrue(passwordHasher.matches("isolated-test-password", firstHash));
        assertFalse(passwordHasher.matches("different-password", firstHash));
        assertFalse(passwordHasher.matches("isolated-test-password", "plaintext"));
        assertFalse(passwordHasher.matches("isolated-test-password", null));
        assertFalse(passwordHasher.matches("isolated-test-password", "$pbkdf2-sha256$210000$salt"));
        assertFalse(passwordHasher.matches("isolated-test-password", "$pbkdf2-sha256$invalid$salt$hash"));
        assertFalse(passwordHasher.matches("isolated-test-password", "$pbkdf2-sha256$1$salt$AA=="));
        assertFalse(passwordHasher.matches("isolated-test-password", "$pbkdf2-sha256$210000$%%%$AA=="));
        assertFalse(firstHash.equals(secondHash));
    }

    @Test
    void logsInWhenPasswordContainsQuote() throws Exception {
        String username = "quote-user-" + UUID.randomUUID();
        String password = "correct'password";
        String dbUrl = System.getenv().getOrDefault("AUTH_DB_URL", "jdbc:sqlite:./data/workshop.db");

        try (Connection connection = DriverManager.getConnection(dbUrl);
             PreparedStatement insertUser = connection.prepareStatement(
                     "INSERT INTO legacy_users(username,password,display_name,role) VALUES (?,?,?,?)")) {
            insertUser.setString(1, username);
            insertUser.setString(2, passwordHasher.hash(password));
            insertUser.setString(3, "Quote Test User");
            insertUser.setString(4, "STUDENT");
            insertUser.executeUpdate();

            given()
                    .contentType("application/json")
                    .body("{\"username\":\"" + username + "\",\"password\":\"" + password + "\"}")
                    .when().post("/auth/login")
                    .then()
                    .statusCode(200)
                    .body("user.username", is(username))
                    .body("token", notNullValue());
        } finally {
            try (Connection connection = DriverManager.getConnection(dbUrl);
                 PreparedStatement deleteUser = connection.prepareStatement(
                         "DELETE FROM legacy_users WHERE username=?")) {
                deleteUser.setString(1, username);
                deleteUser.executeUpdate();
            }
        }
    }
}
