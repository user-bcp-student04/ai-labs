package com.bcp.workshop.auth;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import jakarta.annotation.PostConstruct;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.inject.Inject;
import org.eclipse.microprofile.config.inject.ConfigProperty;

import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;
import java.nio.charset.StandardCharsets;
import java.security.GeneralSecurityException;
import java.time.Instant;
import java.util.Base64;
import java.util.Map;

@ApplicationScoped
public class TokenService {
    static final int EXPIRATION_SECONDS = 3600;
    private static final String SIGNATURE_ALGORITHM = "HmacSHA256";
    private static final String TOKEN_ALGORITHM = "HS256";
    private static final String TOKEN_TYPE = "JWT";
    private static final Base64.Encoder BASE64_URL_ENCODER = Base64.getUrlEncoder().withoutPadding();

    @ConfigProperty(name = "auth.token.secret")
    String secret;

    @Inject
    ObjectMapper objectMapper;

    @PostConstruct
    void validateSecret() {
        if (secret == null || secret.getBytes(StandardCharsets.UTF_8).length < 32) {
            throw new IllegalStateException("Authentication token secret must contain at least 32 bytes");
        }
    }

    public String create(String username, String role) throws JsonProcessingException, GeneralSecurityException {
        long expiry = Instant.now().plusSeconds(EXPIRATION_SECONDS).getEpochSecond();
        String header = encodeJson(Map.of("alg", TOKEN_ALGORITHM, "typ", TOKEN_TYPE));
        String payload = encodeJson(Map.of("sub", username, "role", role, "exp", expiry));
        String signingInput = header + "." + payload;
        String signature = BASE64_URL_ENCODER.encodeToString(sign(signingInput));
        return signingInput + "." + signature;
    }

    private String encodeJson(Map<String, ?> value) throws JsonProcessingException {
        byte[] json = objectMapper.writeValueAsBytes(value);
        return BASE64_URL_ENCODER.encodeToString(json);
    }

    private byte[] sign(String signingInput) throws GeneralSecurityException {
        Mac mac = Mac.getInstance(SIGNATURE_ALGORITHM);
        mac.init(new SecretKeySpec(secret.getBytes(StandardCharsets.UTF_8), SIGNATURE_ALGORITHM));
        return mac.doFinal(signingInput.getBytes(StandardCharsets.US_ASCII));
    }
}
