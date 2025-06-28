package com.github.avatar.controller;

import com.github.avatar.dto.UserAddDTO;
import com.github.avatar.dto.UserDTO;
import com.github.avatar.dto.UserSearchDTO;
import com.github.avatar.service.KeycloakService;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.oauth2.jwt.Jwt;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
public class UserController {
    private final KeycloakService keycloakService;

    public UserController(KeycloakService keycloakService) {
        this.keycloakService = keycloakService;
    }


    @GetMapping("/users")
    public List<UserDTO> getUsers(@ModelAttribute UserSearchDTO userSearchDTO) {
        return keycloakService.getUsers(userSearchDTO);
    }

    @PostMapping("/users")
    public ResponseEntity<Void> addUserToGroup(@AuthenticationPrincipal Jwt jwt, @RequestBody UserAddDTO userAddDTO) {
        if (!jwt.getSubject().equals(keycloakService.getGroupOwnerIdByGroupId(userAddDTO.groupId()))) {
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED).build();
        }
        for (String userId : userAddDTO.userIds()) {
            keycloakService.addUserToGroup(userAddDTO.groupId(), userId);
        }
        return ResponseEntity.status(HttpStatus.OK).build();
    }

    @PostMapping("/language")
    public void setLanguage(@AuthenticationPrincipal Jwt jwt, @RequestBody String language) {
        keycloakService.setLanguage(jwt, language);
    }
}
