package com.github.avatar.controller;

import com.github.avatar.dto.UserDTO;
import com.github.avatar.dto.UserSearchDTO;
import com.github.avatar.service.KeycloakService;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.ModelAttribute;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;

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
}
