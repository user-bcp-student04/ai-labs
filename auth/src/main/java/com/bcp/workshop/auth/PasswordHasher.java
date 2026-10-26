package com.bcp.workshop.auth;

import jakarta.enterprise.context.ApplicationScoped;

import javax.crypto.SecretKeyFactory;
import javax.crypto.spec.PBEKeySpec;
import java.security.GeneralSecurityException;
import java.security.MessageDigest;
import java.security.SecureRandom;
import java.util.Base64;

@ApplicationScoped
public class PasswordHasher {
    private static final String HASH_PREFIX = "$pbkdf2-sha256$";
    private static final String KEY_ALGORITHM = "PBKDF2WithHmacSHA256";
    private static final int ITERATIONS = 210_000;
    private static final int SALT_LENGTH_BYTES = 16;
    private static final int HASH_LENGTH_BYTES = 32;
    private static final int MINIMUM_ACCEPTED_ITERATIONS = 100_000;
    private static final int MAXIMUM_ACCEPTED_ITERATIONS = 500_000;

    private final SecureRandom secureRandom = new SecureRandom();

    public String hash(String password) {
        byte[] salt = new byte[SALT_LENGTH_BYTES];
        secureRandom.nextBytes(salt);
        byte[] derivedKey = deriveKey(password, salt, ITERATIONS);
        return HASH_PREFIX + ITERATIONS + "$"
                + Base64.getEncoder().encodeToString(salt) + "$"
                + Base64.getEncoder().encodeToString(derivedKey);
    }

    public boolean matches(String password, String encodedHash) {
        if (!isHashed(encodedHash)) {
            return false;
        }

        String[] parts = encodedHash.split("\\$", -1);
        if (parts.length != 5) {
            return false;
        }

        int iterations = parseIterations(parts[2]);
        if (iterations < MINIMUM_ACCEPTED_ITERATIONS || iterations > MAXIMUM_ACCEPTED_ITERATIONS) {
            return false;
        }

        byte[] salt = decode(parts[3]);
        byte[] expectedHash = decode(parts[4]);
        if (salt == null || expectedHash == null || expectedHash.length != HASH_LENGTH_BYTES) {
            return false;
        }

        byte[] actualHash = deriveKey(password, salt, iterations);
        return MessageDigest.isEqual(expectedHash, actualHash);
    }

    public boolean isHashed(String value) {
        if (value == null) {
            return false;
        }

        String[] parts = value.split("\\$", -1);
        if (parts.length != 5 || !"pbkdf2-sha256".equals(parts[1])) {
            return false;
        }

        int iterations = parseIterations(parts[2]);
        byte[] salt = decode(parts[3]);
        byte[] expectedHash = decode(parts[4]);
        return iterations >= MINIMUM_ACCEPTED_ITERATIONS
                && iterations <= MAXIMUM_ACCEPTED_ITERATIONS
                && salt != null
                && salt.length == SALT_LENGTH_BYTES
                && expectedHash != null
                && expectedHash.length == HASH_LENGTH_BYTES;
    }

    private int parseIterations(String value) {
        try {
            return Integer.parseInt(value);
        } catch (NumberFormatException ignored) {
            return 0;
        }
    }

    private byte[] decode(String value) {
        try {
            return Base64.getDecoder().decode(value);
        } catch (IllegalArgumentException ignored) {
            return null;
        }
    }

    private byte[] deriveKey(String password, byte[] salt, int iterations) {
        PBEKeySpec keySpec = new PBEKeySpec(
                password.toCharArray(),
                salt,
                iterations,
                HASH_LENGTH_BYTES * Byte.SIZE);
        try {
            SecretKeyFactory keyFactory = SecretKeyFactory.getInstance(KEY_ALGORITHM);
            return keyFactory.generateSecret(keySpec).getEncoded();
        } catch (GeneralSecurityException error) {
            throw new IllegalStateException("Password hashing is unavailable", error);
        } finally {
            keySpec.clearPassword();
        }
    }
}
