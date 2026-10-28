package com.bcp.workshop.auth;

import jakarta.annotation.PostConstruct;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.inject.Inject;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;
import java.util.ArrayList;
import java.util.List;

@ApplicationScoped
public class LegacyDatabase {
    private static final String DB_URL = System.getenv().getOrDefault("AUTH_DB_URL", "jdbc:sqlite:./data/workshop.db");
    private static final String STORAGE_COLUMN = "password_storage";
    private static final String STORAGE_LEGACY = "LEGACY";
    private static final String STORAGE_HASHED = "HASHED";

    @Inject
    PasswordHasher passwordHasher;

    @PostConstruct
    void initialize() {
        try {
            Files.createDirectories(Path.of("data"));
            try (Connection connection = DriverManager.getConnection(DB_URL)) {
                connection.setAutoCommit(false);
                try {
                    createSchema(connection);
                    insertSeedUserIfMissing(connection, "student", "Workshop123!", "Workshop Student", "STUDENT");
                    insertSeedUserIfMissing(connection, "trainer", "Trainer123!", "Workshop Trainer", "TRAINER");
                    migrateLegacyPasswords(connection);
                    connection.commit();
                } catch (SQLException | RuntimeException error) {
                    rollback(connection, error);
                    throw error;
                }
            }
        } catch (IOException | SQLException | RuntimeException error) {
            throw new IllegalStateException("Unable to initialize authentication database", error);
        }
    }

    private void createSchema(Connection connection) throws SQLException {
        try (Statement statement = connection.createStatement()) {
            statement.executeUpdate("CREATE TABLE IF NOT EXISTS legacy_users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT NOT NULL, display_name TEXT NOT NULL, role TEXT NOT NULL, password_storage TEXT NOT NULL DEFAULT '" + STORAGE_LEGACY + "')");
        }
        if (!hasColumn(connection, STORAGE_COLUMN)) {
            addStorageColumn(connection);
        }
    }

    private boolean hasColumn(Connection connection, String columnName) throws SQLException {
        try (PreparedStatement columns = connection.prepareStatement("PRAGMA table_info(legacy_users)");
             ResultSet result = columns.executeQuery()) {
            while (result.next()) {
                if (columnName.equals(result.getString("name"))) {
                    return true;
                }
            }
        }
        return false;
    }

    private void addStorageColumn(Connection connection) throws SQLException {
        try (Statement statement = connection.createStatement()) {
            statement.executeUpdate("ALTER TABLE legacy_users ADD COLUMN " + STORAGE_COLUMN
                    + " TEXT NOT NULL DEFAULT '" + STORAGE_LEGACY + "'");
        }
        markExistingHashes(connection);
    }

    private void markExistingHashes(Connection connection) throws SQLException {
        List<Long> hashedIds = new ArrayList<>();
        try (PreparedStatement findPasswords = connection.prepareStatement("SELECT id, password FROM legacy_users");
             ResultSet result = findPasswords.executeQuery()) {
            while (result.next()) {
                if (passwordHasher.isHashed(result.getString("password"))) {
                    hashedIds.add(result.getLong("id"));
                }
            }
        }
        try (PreparedStatement markHashed = connection.prepareStatement(
                "UPDATE legacy_users SET " + STORAGE_COLUMN + "=? WHERE id=?")) {
            for (Long id : hashedIds) {
                markHashed.setString(1, STORAGE_HASHED);
                markHashed.setLong(2, id);
                markHashed.executeUpdate();
            }
        }
    }

    private void insertSeedUserIfMissing(
            Connection connection, String username, String password, String displayName, String role) throws SQLException {
        try (PreparedStatement findUser = connection.prepareStatement(
                "SELECT 1 FROM legacy_users WHERE username=?")) {
            findUser.setString(1, username);
            try (ResultSet existingUser = findUser.executeQuery()) {
                if (existingUser.next()) {
                    return;
                }
            }
        }

        try (PreparedStatement insertUser = connection.prepareStatement(
                "INSERT INTO legacy_users(username,password,display_name,role) VALUES (?,?,?,?)")) {
            insertUser.setString(1, username);
            insertUser.setString(2, passwordHasher.hash(password));
            insertUser.setString(3, displayName);
            insertUser.setString(4, role);
            insertUser.executeUpdate();
        }
    }

    private void migrateLegacyPasswords(Connection connection) throws SQLException {
        List<LegacyPassword> legacyPasswords = findLegacyPasswords(connection);
        try (PreparedStatement updatePassword = connection.prepareStatement(
                "UPDATE legacy_users SET password=?, password_storage=? WHERE id=?")) {
            for (LegacyPassword legacyPassword : legacyPasswords) {
                updatePassword.setString(1, passwordHasher.hash(legacyPassword.password()));
                updatePassword.setString(2, STORAGE_HASHED);
                updatePassword.setLong(3, legacyPassword.id());
                updatePassword.executeUpdate();
            }
        }
    }

    private List<LegacyPassword> findLegacyPasswords(Connection connection) throws SQLException {
        List<LegacyPassword> legacyPasswords = new ArrayList<>();
        try (PreparedStatement findPasswords = connection.prepareStatement(
                "SELECT id, password FROM legacy_users WHERE " + STORAGE_COLUMN + "=?")) {
            findPasswords.setString(1, STORAGE_LEGACY);
            try (ResultSet result = findPasswords.executeQuery()) {
                while (result.next()) {
                    legacyPasswords.add(new LegacyPassword(result.getLong("id"), result.getString("password")));
                }
            }
        }
        return legacyPasswords;
    }

    private void rollback(Connection connection, Exception cause) {
        try {
            connection.rollback();
        } catch (SQLException rollbackError) {
            cause.addSuppressed(rollbackError);
        }
    }

    public UserRecord findByCredentials(String username, String password) throws SQLException {
        String sql = "SELECT id, username, password, display_name, role FROM legacy_users WHERE username=?";
        try (Connection connection = DriverManager.getConnection(DB_URL);
             PreparedStatement statement = connection.prepareStatement(sql)) {
            statement.setString(1, username);
            try (ResultSet result = statement.executeQuery()) {
                if (!result.next() || !passwordHasher.matches(password, result.getString("password"))) {
                    return null;
                }
                return new UserRecord(result.getLong("id"), result.getString("username"), result.getString("display_name"), result.getString("role"));
            }
        }
    }

    private record LegacyPassword(long id, String password) {}
}
