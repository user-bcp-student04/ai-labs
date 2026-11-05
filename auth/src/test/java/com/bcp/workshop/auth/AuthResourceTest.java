package com.bcp.workshop.auth;

import io.quarkus.test.junit.QuarkusTest;
import io.restassured.response.ValidatableResponse;
import org.junit.jupiter.api.Test;

import java.util.Map;

import static io.restassured.RestAssured.given;
import static org.hamcrest.CoreMatchers.is;
import static org.hamcrest.Matchers.notNullValue;
import static org.hamcrest.Matchers.nullValue;

@QuarkusTest
class AuthResourceTest {
    @Test
    void logsInWithWorkshopUser() {
        given()
                .contentType("application/json")
                .body("{\"username\":\"student\",\"password\":\"Workshop123!\",\"client\":\"angular-workshop\"}")
                .when().post("/auth/login")
                .then()
                .statusCode(200)
                .body("user.username", is("student"))
                .body("token", notNullValue());
    }

    // Requisito "Credenciales válidas inician sesión": segundo usuario sembrado.
    @Test
    void logsInWithTrainerUser() {
        login("trainer", "Trainer123!")
                .statusCode(200)
                .body("user.username", is("trainer"))
                .body("token", notNullValue());
    }

    // Requisito "Credenciales inválidas se rechazan": contraseña que no coincide.
    @Test
    void rejectsWrongPassword() {
        login("student", "incorrecta")
                .statusCode(401)
                .body("token", nullValue());
    }

    // Requisito "Credenciales inválidas se rechazan": usuario que no existe.
    @Test
    void rejectsUnknownUser() {
        login("noexiste", "Workshop123!")
                .statusCode(401)
                .body("token", nullValue());
    }

    // Requisito "Validación de entrada preservada": username vacío.
    @Test
    void rejectsEmptyUsername() {
        login("", "Workshop123!")
                .statusCode(400)
                .body("message", is("Username is required"));
    }

    // Requisito "Validación de entrada preservada": password vacío.
    @Test
    void rejectsEmptyPassword() {
        login("student", "")
                .statusCode(400)
                .body("message", is("Password is required"));
    }

    // Requisito "Los valores de credenciales no alteran la consulta": inyección en usuario.
    @Test
    void rejectsSqlInjectionInUsername() {
        login("' OR '1'='1", "cualquiera")
                .statusCode(401)
                .body("token", nullValue());
    }

    // Requisito "Los valores de credenciales no alteran la consulta": inyección en contraseña.
    @Test
    void rejectsSqlInjectionInPassword() {
        login("student", "' OR '1'='1")
                .statusCode(401)
                .body("token", nullValue());
    }

    // Requisito "Los valores de credenciales no alteran la consulta": comentario SQL.
    @Test
    void rejectsSqlCommentInjectionInUsername() {
        login("student'--", "cualquiera")
                .statusCode(401)
                .body("token", nullValue());
    }

    private static ValidatableResponse login(String username, String password) {
        return given()
                .contentType("application/json")
                .body(Map.of("username", username, "password", password))
                .when().post("/auth/login")
                .then();
    }
}
