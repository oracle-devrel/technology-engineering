package com.example.fn;

import com.fnproject.fn.api.FnConfiguration;
import com.fnproject.fn.api.Headers;
import com.fnproject.fn.api.InputEvent;

import com.fnproject.fn.api.RuntimeContext;
import com.fnproject.fn.api.httpgateway.HTTPGatewayContext;

import java.io.*;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.Arrays;
import java.util.Base64;
import java.util.List;
import java.util.stream.Collectors;

public class HelloFunction {

    String authConfig = "";

    @FnConfiguration
    public void setUp(RuntimeContext ctx) throws Exception {
        authConfig = ctx.getConfigurationByKey("config").orElse(System.getenv().getOrDefault("config", ""));
    }

    public String handleRequest(final HTTPGatewayContext hctx, final InputEvent input) {

        boolean IS_FOUND = false;
        String ret = "";
        String username = "";

        String body = input.consumeBody((InputStream is) -> {
            try (BufferedReader reader = new BufferedReader(new InputStreamReader(is))) {
                return reader.lines().collect(Collectors.joining());
            } catch (IOException e) {
                throw new RuntimeException(e);
            }
        });
        System.out.println("Body: " + body);

        String[] configTokens = authConfig.split(",");
        List<String> tokenizedConfig = Arrays.stream(configTokens).map(String::trim).collect(Collectors.toList());

        if(body.length() > 0) {
            String[] bodyTokens = body.split(",");
            List<String> tokenizedBody = Arrays.stream(bodyTokens).map(String::trim).collect(Collectors.toList());

            for (String configToken : tokenizedConfig) {
                for (String token : tokenizedBody) {
                    if (token.indexOf("Basic ") > -1 && configToken.length() > 0) {
                        String auth_token = token.substring(token.indexOf("Basic ") + 6, token.indexOf("\"}"));
                        if (auth_token.equals(configToken)) {
                            System.out.println("AUTH SUCCESS " + auth_token + " == " + configToken);
                            byte[] decodedBytes = Base64.getDecoder().decode(auth_token);
                            String decodedString = new String(decodedBytes);
                            String[] decodedTokens = decodedString.split(":");
                            username = decodedTokens[0];
                            IS_FOUND = true;
                        } else {
                            System.out.println("AUTH NO MATCH " + auth_token + " <> " + configToken);
                        }
                    }
                }
            }
        }

        // Use header transformation in APIGW Route to get username in headers from this response
        // in the target function:
        // Overwrite	username     ${request.auth[username]}
        if(IS_FOUND) {
            LocalDateTime dateTime = LocalDateTime.now().plusDays(1);
            DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyy-MM-dd'T'HH:mm:ss'+00:00'");
            String expiryDate = dateTime.format(formatter);
            ret = "{ " +
                    "\"active\": true," +
                    "\"principal\": \"myprincipal\"," +
                    "\"scope\": [\"fnbasicauthtest\"]," +
                    "\"expiresAt\": \"" + expiryDate + "\"," +
                    "\"context\": { \"username\": \"" + username + "\" }" +
                    " }";
        } else {
            ret = "{ " +
                    "\"active\": false," +
                    "\"wwwAuthenticate\": \"Basic realm=\\\"fnbasicauthtest.io\\\"\"" +
                    " }";
        }
        System.out.println(ret);
        return ret;
    }
}