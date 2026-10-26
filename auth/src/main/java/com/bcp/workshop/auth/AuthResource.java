package com.bcp.workshop.auth;

import jakarta.inject.Inject;
import jakarta.ws.rs.Consumes;
import jakarta.ws.rs.POST;
import jakarta.ws.rs.Path;
import jakarta.ws.rs.Produces;
import jakarta.ws.rs.core.MediaType;
import jakarta.ws.rs.core.Response;
import org.jboss.logging.Logger;

import java.util.Map;

@Path("/auth")
@Consumes(MediaType.APPLICATION_JSON)
@Produces(MediaType.APPLICATION_JSON)
public class AuthResource {
    private static final Logger LOGGER = Logger.getLogger(AuthResource.class);

    @Inject
    AuthService authService;

    @POST
    @Path("/login")
    public Response login(LoginRequest request) {
        try {
            AuthService.LoginOutcome outcome = authService.login(request);
            if (outcome.status() == AuthService.LoginStatus.AUTHENTICATED) {
                return Response.ok(outcome.response()).build();
            }

            return Response.status(outcome.status().httpStatus())
                    .entity(Map.of("message", outcome.message()))
                    .build();
        } catch (Exception error) {
            LOGGER.error("Login request failed", error);
            return Response.status(500).entity(Map.of(
                    "message", "Authentication service error",
                    "exception", "InternalServerError"
            )).build();
        }
    }
}
