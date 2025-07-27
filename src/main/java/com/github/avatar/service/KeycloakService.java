package com.github.avatar.service;

import com.github.avatar.dto.RoomCreationDTO;
import com.github.avatar.dto.RoomDTO;
import com.github.avatar.dto.UserDTO;
import com.github.avatar.dto.UserSearchDTO;
import jakarta.annotation.Nullable;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.security.oauth2.jwt.Jwt;
import org.springframework.stereotype.Service;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.web.reactive.function.client.WebClient;
import org.springframework.web.reactive.function.client.WebClientResponseException;
import org.springframework.web.util.UriComponentsBuilder;
import reactor.core.publisher.Mono;

import java.net.URI;
import java.util.*;

@Service
public class KeycloakService {
    @Value("${keycloak.admin-url}")
    private String adminUrl;

    @Value("${keycloak.admin-token}")
    private String adminToken;

    @Value("${keycloak.token-url}")
    private String tokenUrl;

    public List<RoomDTO> findAllRooms(Jwt jwt) {
        List<String> groupPaths = jwt.getClaimAsStringList("groups");
        if (groupPaths == null || groupPaths.isEmpty()) {
            return Collections.emptyList();
        }

        List<RoomDTO> rooms = new ArrayList<>();
        for (String groupPath : groupPaths) {
            rooms.add(fetchGroupInfo(groupPath));
        }
        return rooms;
    }

    private RoomDTO createRoomPath(int year, String semester, String lastName, String roomName, Map<String, List<String>> attributes) {
        RoomDTO yearGroup = getOrCreateGroup("/" + year, String.valueOf(year), Collections.emptyMap());
        RoomDTO semesterGroup = getOrCreateSubGroup(yearGroup.id(), "/" + year + "/" + semester, String.valueOf(semester), Collections.emptyMap());
        RoomDTO lastNameGroup = getOrCreateSubGroup(semesterGroup.id(), "/" + year + "/" + semester + "/" + lastName, lastName, Collections.emptyMap());
        return getOrCreateSubGroup(lastNameGroup.id(), "/" + year + "/" + semester + "/" + lastName + "/" + roomName, roomName, attributes);
    }

    private RoomDTO getOrCreateGroup(String path, String name, Map<String, List<String>> attributes) {
        try {
            return fetchGroupInfo(path);
        } catch(WebClientResponseException e) {
            createGroup(path, name, attributes);
            return fetchGroupInfo(path);
        }
    }

    private RoomDTO getOrCreateSubGroup(@Nullable String parent, String path, String name, Map<String, List<String>> attributes) {
        try {
            return fetchGroupInfo(path);
        } catch(WebClientResponseException e) {
            createSubGroup(parent, path, name, attributes);
            return fetchGroupInfo(path);
        }
    }

    private void createSubGroup(String parent, String path, String name, Map<String, List<String>> attributes) {
        String token = getAdminAccessToken();
        WebClient webClient = WebClient.builder().build();

        Map<String, Object> body = new LinkedHashMap<>();
        body.put("name", name);
        body.put("path", path);
        body.put("attributes", attributes);
        body.put("parentId", parent);

        webClient.post()
                .uri(adminUrl + "/groups/" + parent + "/children")
                .body(Mono.just(body), Map.class)
                .header(HttpHeaders.AUTHORIZATION, "Bearer " + token)
                .retrieve()
                .bodyToMono(Void.class)
                .block();
    }

    private void createGroup(String path, String name, Map<String, List<String>> attributes) {
        String token = getAdminAccessToken();
        WebClient webClient = WebClient.builder().build();

        Map<String, Object> body = new LinkedHashMap<>();
        body.put("name", name);
        body.put("path", path);
        body.put("attributes", attributes);

        webClient.post()
                .uri(adminUrl + "/groups")
                .body(Mono.just(body), Map.class)
                .header(HttpHeaders.AUTHORIZATION, "Bearer " + token)
                .retrieve()
                .bodyToMono(Void.class)
                .block();
    }

    public RoomDTO createRoom(Jwt jwt, RoomCreationDTO roomDTO) {
        Map<String, List<String>> attributes = new HashMap<>();
        attributes.put("owner", List.of(jwt.getSubject()));
        attributes.put("icon", List.of(roomDTO.icon()));

        RoomDTO room = createRoomPath(
            roomDTO.year(),
            roomDTO.semester(),
            jwt.getClaim("family_name"),
            roomDTO.name(),
            attributes
        );

        // Add the creator as a member of the group
        addUserToGroup(room.id(), jwt.getSubject());

        return room;
    }

    private RoomDTO fetchGroupInfo(String path) {
        String token = getAdminAccessToken();
        WebClient webClient = WebClient.builder().build();

        var group = webClient.get()
                .uri(adminUrl + "/group-by-path" + path)
                .header(HttpHeaders.AUTHORIZATION, "Bearer " + token)
                .retrieve()
                .bodyToMono(new ParameterizedTypeReference<Map<String, Object>>() {})
                .block();

        Map<String, List<String>> attributes = (Map<String, List<String>>) group.get("attributes");
        return new RoomDTO(group.get("id").toString(), path, (String) group.get("name"), attributes);
    }

    public String getGroupOwnerIdByGroupId(String groupId) {
        String token = getAdminAccessToken();
        WebClient webClient = WebClient.builder().build();

        var group = webClient.get()
                .uri(adminUrl + "/groups/" + groupId)
                .header(HttpHeaders.AUTHORIZATION, "Bearer " + token)
                .retrieve()
                .bodyToMono(new ParameterizedTypeReference<Map<String, Object>>() {})
                .block();
        if (group == null || group.isEmpty() || !group.containsKey("attributes")) {
            return "";
        }
        return ((List<String>)((Map<?, ?>) group.get("attributes")).get("owner")).get(0);
    }

    public String getGroupOwnerIdByGroupPath(String groupPath) {
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

    public void setLanguage(Jwt jwt, String language) {
        String token = getAdminAccessToken();
        WebClient webClient = WebClient.builder().build();

        Map<String, Object> body = getUser(jwt.getSubject());
        body.put("attributes", Map.of("language", List.of(language)));

        webClient.put()
                .uri(adminUrl + "/users/" + jwt.getSubject())
                .body(Mono.just(body), Map.class)
                .header(HttpHeaders.AUTHORIZATION, "Bearer " + token)
                .retrieve()
                .bodyToMono(Void.class)
                .block();
    }

    public Map<String, Object> getUser(String userId) {
        String token = getAdminAccessToken();
        WebClient webClient = WebClient.builder().build();

        return webClient.get()
                .uri(adminUrl + "/users/" + userId)
                .header(HttpHeaders.AUTHORIZATION, "Bearer " + token)
                .retrieve()
                .bodyToMono(new ParameterizedTypeReference<Map<String, Object>>() {})
                .block();
    }

    public void addUserToGroup(String groupId, String userId) {
        String token = getAdminAccessToken();
        WebClient webClient = WebClient.builder().build();

        webClient.put()
                .uri(adminUrl + "/users/" + userId + "/groups/" +  groupId)
                .header(HttpHeaders.AUTHORIZATION, "Bearer " + token)
                .retrieve()
                .bodyToMono(Void.class)
                .block();
    }

    public List<UserDTO> getUsers(UserSearchDTO userSearchDTO) {
        String token = getAdminAccessToken();
        WebClient webClient = WebClient.builder().build();
        MultiValueMap<String, String> queryParams = new LinkedMultiValueMap<>();

        if (userSearchDTO.firstName() != null) {
            queryParams.add("firstName", userSearchDTO.firstName());
        }

        if (userSearchDTO.lastName() != null) {
            queryParams.add("lastName", userSearchDTO.lastName());
        }

        if (userSearchDTO.email() != null) {
            queryParams.add("email", userSearchDTO.email());
        }

        if (userSearchDTO.first() != null) {
            queryParams.add("first", userSearchDTO.first().toString());
        }

        URI uri = UriComponentsBuilder.fromHttpUrl(adminUrl + "/users").queryParams(queryParams).build().toUri();
        return webClient.get()
                .uri(uri)
                .header(HttpHeaders.AUTHORIZATION, "Bearer " + token)
                .retrieve()
                .bodyToMono(new ParameterizedTypeReference<List<UserDTO>>() {})
                .block();
    }
}
