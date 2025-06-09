package com.github.avatar.service;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Service;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.web.reactive.function.client.WebClient;

import java.util.List;
import java.util.Map;

@Service
public class KeycloakService {
    @Value("${keycloak.admin-url}")
    private String adminUrl;

    @Value("${keycloak.admin-token}")
    private String adminToken;

    @Value("${keycloak.token-url}")
    private String tokenUrl;

    public String getGroupOwnerId(String groupPath) {
        String token = getAdminAccessToken();
        WebClient webClient = WebClient.builder().build();

        var group = webClient.get()
                .uri(adminUrl + "/group-by-path" + groupPath)
                .header(HttpHeaders.AUTHORIZATION, "Bearer " + token)
                .retrieve()
                .bodyToMono(new ParameterizedTypeReference<Map<String, Object>>() {})
                .block();
        if (group == null || group.isEmpty() || !group.containsKey("attributes")) {
            return "";
        }
        return ((List<String>)((Map<?, ?>) group.get("attributes")).get("owner")).get(0);
    }

    public String getAdminAccessToken() {
        WebClient webClient = WebClient.builder().build();

        MultiValueMap<String, String> formData = new LinkedMultiValueMap<>();
        formData.add("grant_type", "client_credentials");
        formData.add("client_id", "backend-client");
        formData.add("client_secret", adminToken);

        return webClient.post()
                .uri(tokenUrl)
                .contentType(MediaType.APPLICATION_FORM_URLENCODED)
                .bodyValue(formData)
                .retrieve()
                .bodyToMono(Map.class)
                .map(response -> (String) response.get("access_token"))
                .block();
    }
}
