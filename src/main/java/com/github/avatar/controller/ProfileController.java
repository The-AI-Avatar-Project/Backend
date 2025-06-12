package com.github.avatar.controller;

import com.github.avatar.service.ProfileService;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;
import org.springframework.security.oauth2.jwt.Jwt;

import java.io.IOException;

@RestController
@RequestMapping("/profile")
public class ProfileController {

    private final ProfileService profileService;

    public ProfileController(ProfileService profileService) {
        this.profileService = profileService;
    }

    @PostMapping("/{keycloakUserId}/upload")
    public ResponseEntity<String> uploadFiles(
            @PathVariable String keycloakUserId,
            @RequestParam("files") MultipartFile[] files,
            @AuthenticationPrincipal Jwt jwt) {

        String loggedInUserId = jwt.getSubject();

        if (!loggedInUserId.equals(keycloakUserId)) {
            return ResponseEntity.status(403).body("Permission denied: You can only edit your own profile");
        }

        try {
            profileService.saveFiles(keycloakUserId, files);
            return ResponseEntity.ok("Uploaded files successfully.");
        } catch (IOException e) {
            return ResponseEntity.status(500).body("Error while saving files: " + e.getMessage());
        }
    }
}
