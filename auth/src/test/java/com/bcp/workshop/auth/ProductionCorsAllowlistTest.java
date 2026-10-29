package com.bcp.workshop.auth;

import static io.restassured.RestAssured.given;
import static org.hamcrest.Matchers.nullValue;

import io.quarkus.test.junit.QuarkusTest;
import io.quarkus.test.junit.QuarkusTestProfile;
import io.quarkus.test.junit.TestProfile;
import java.util.Map;
import org.junit.jupiter.api.Test;

@QuarkusTest
@TestProfile(ProductionCorsAllowlistTest.ProductionCorsProfile.class)
class ProductionCorsAllowlistTest {

    @Test
    void emptyProductionAllowlistGrantsNoCorsToDevelopmentOrigin() {
        given()
                .header("Origin", "http://localhost:4200")
                .header("Access-Control-Request-Method", "POST")
                .header("Access-Control-Request-Headers", "content-type")
                .when().options("/auth/login")
                .then()
                .header("Access-Control-Allow-Origin", nullValue())
                .header("Access-Control-Allow-Credentials", nullValue());
    }

    public static class ProductionCorsProfile implements QuarkusTestProfile {

        @Override
        public Map<String, String> getConfigOverrides() {
            return Map.of(
                    "quarkus.http.cors.origins", "",
                    "auth.token.secret", "production-profile-isolated-test-secret-0123456789");
        }
    }
}
