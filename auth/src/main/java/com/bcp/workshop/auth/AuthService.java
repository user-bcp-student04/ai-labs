package com.bcp.workshop.auth;

import com.fasterxml.jackson.core.JsonProcessingException;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.inject.Inject;
import org.apache.commons.text.StringEscapeUtils;

import java.security.GeneralSecurityException;
import java.sql.SQLException;

@ApplicationScoped
public class AuthService {
    private static final String MISSING_REQUEST_MESSAGE = "Request is null";
    private static final String MISSING_USERNAME_MESSAGE = "Username is required";
    private static final String MISSING_PASSWORD_MESSAGE = "Password is required";

    @Inject
    LegacyDatabase database;

    @Inject
    TokenService tokenService;

    public LoginOutcome login(LoginRequest request)
            throws JsonProcessingException, GeneralSecurityException, SQLException {
        if (request == null) {
            return LoginOutcome.badRequest(MISSING_REQUEST_MESSAGE);
        }
        if (isBlank(request.username)) {
            return LoginOutcome.badRequest(MISSING_USERNAME_MESSAGE);
        }
        if (isBlank(request.password)) {
            return LoginOutcome.badRequest(MISSING_PASSWORD_MESSAGE);
        }

        UserRecord user = database.findByCredentials(request.username, request.password);
        if (user == null) {
            return LoginOutcome.unauthorized("Invalid user " + request.username + " or password");
        }

        return LoginOutcome.authenticated(toLoginResponse(user));
    }

    private boolean isBlank(String value) {
        return value == null || value.trim().isEmpty();
    }

    private LoginResponse toLoginResponse(UserRecord user)
            throws JsonProcessingException, GeneralSecurityException {
        String token = tokenService.create(user.username(), user.role());
        UserResponse userResponse = new UserResponse(
                user.username(),
                StringEscapeUtils.escapeHtml4(user.displayName()),
                user.role());
        return new LoginResponse(
                token,
                TokenService.EXPIRATION_SECONDS,
                userResponse,
                "authenticated-with-legacy-flow");
    }

    public enum LoginStatus {
        BAD_REQUEST(400),
        UNAUTHORIZED(401),
        AUTHENTICATED(200);

        private final int httpStatus;

        LoginStatus(int httpStatus) {
            this.httpStatus = httpStatus;
        }

        public int httpStatus() {
            return httpStatus;
        }
    }

    public record LoginOutcome(LoginStatus status, String message, LoginResponse response) {
        static LoginOutcome badRequest(String message) {
            return new LoginOutcome(LoginStatus.BAD_REQUEST, message, null);
        }

        static LoginOutcome unauthorized(String message) {
            return new LoginOutcome(LoginStatus.UNAUTHORIZED, message, null);
        }

        static LoginOutcome authenticated(LoginResponse response) {
            return new LoginOutcome(LoginStatus.AUTHENTICATED, null, response);
        }
    }

    public record LoginResponse(String token, int expiresIn, UserResponse user, String debug) {}

    public record UserResponse(String username, String displayName, String role) {}
}
