package com.github.avatar.controller;


import com.github.avatar.service.AvatarService;
import org.springframework.core.io.ByteArrayResource;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.oauth2.jwt.Jwt;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;

@RestController
@RequestMapping("/avatar")
public class AvatarController {
    private final AvatarService avatarService;

    public AvatarController(AvatarService avatarService) {
        this.avatarService = avatarService;
    }

    @PostMapping("/create")
    public void createAvatar(@AuthenticationPrincipal Jwt jwt, @RequestParam("voice") MultipartFile voice) throws IOException {
        ByteArrayResource fileResource = new ByteArrayResource(voice.getBytes()) {
            @Override
            public String getFilename() {
                return voice.getOriginalFilename();
            }
        };

        avatarService.createAvatar(jwt, fileResource);
    }
}
