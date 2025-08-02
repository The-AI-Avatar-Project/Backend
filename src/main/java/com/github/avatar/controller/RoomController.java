package com.github.avatar.controller;

import com.github.avatar.Main;
import com.github.avatar.dto.RoomCreationDTO;
import com.github.avatar.dto.RoomDTO;
import com.github.avatar.service.KeycloakService;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.oauth2.jwt.Jwt;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
public class RoomController {
    private final KeycloakService keycloakService;

    public RoomController(KeycloakService keycloakService) {
        this.keycloakService = keycloakService;
    }

    @GetMapping("/rooms")
    public List<RoomDTO> getRooms(@AuthenticationPrincipal Jwt jwt) {
        return keycloakService.findAllRooms(jwt.getSubject());

    }

    @PostMapping("/rooms")
    public void createRoom(@AuthenticationPrincipal Jwt jwt, @RequestBody RoomCreationDTO room) {
        keycloakService.createRoom(jwt, room);
    }
}
