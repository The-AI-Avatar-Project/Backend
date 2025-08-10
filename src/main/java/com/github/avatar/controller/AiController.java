package com.github.avatar.controller;

import com.github.avatar.dto.AvatarResponse;
import com.github.avatar.service.PipelineService;
import jakarta.servlet.http.HttpServletRequest;
import org.springframework.core.io.ByteArrayResource;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.oauth2.jwt.Jwt;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;

@RestController
@RequestMapping("/ai")
public class AiController {
    private final PipelineService pipelineService;

    public AiController(PipelineService pipelineService) {
        this.pipelineService = pipelineService;
    }

    public record AvatarTextRequest(String text, String roomPath) {}


    @PostMapping("/text")
    public AvatarResponse requestLlmResponse(@AuthenticationPrincipal Jwt jwt, @RequestBody AvatarTextRequest avatarTextRequest) throws InterruptedException {
        return pipelineService.processText(avatarTextRequest.text(), avatarTextRequest.roomPath(), jwt);
    }

    @PostMapping("/audio")
    public AvatarResponse requestSttResponse(@AuthenticationPrincipal Jwt jwt, HttpServletRequest request, @RequestParam("file") MultipartFile file, @RequestParam("roomPath") String roomPath, @RequestParam(value = "chatId", required = false) String chatId) throws IOException, InterruptedException {
        ByteArrayResource fileResource = new ByteArrayResource(file.getBytes()) {
            @Override
            public String getFilename() {
                return file.getOriginalFilename();
            }
        };

        return pipelineService.processAudio(fileResource, roomPath, jwt);
    }
}
