package com.github.avatar.controller;

import com.github.avatar.dto.AvatarResponse;
import com.github.avatar.service.PipelineService;
import com.github.avatar.service.WebSocketHandler;
import jakarta.servlet.http.HttpServletRequest;
import org.springframework.core.io.ByteArrayResource;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;
import org.springframework.web.servlet.mvc.method.annotation.StreamingResponseBody;

import java.io.IOException;
import java.util.Optional;

@RestController
@RequestMapping("/ai")
public class AiController {
    private final PipelineService pipelineService;
    private final WebSocketHandler webSocketHandler;

    public AiController(PipelineService pipelineService, WebSocketHandler webSocketHandler) {
        this.pipelineService = pipelineService;
        this.webSocketHandler = webSocketHandler;
    }

    public record AvatarTextRequest(String text, String roomPath, Optional<String> chatId) {}


    @PostMapping("/text")
    public ResponseEntity<StreamingResponseBody> requestLlmResponse(HttpServletRequest request, @RequestBody AvatarTextRequest avatarTextRequest) throws IOException {
        AvatarResponse response = pipelineService.processText(avatarTextRequest.text(), avatarTextRequest.roomPath(), avatarTextRequest.chatId().orElse(""));
        String clientIp = request.getRemoteAddr();
        webSocketHandler.sendToIp(clientIp, response);

        return ResponseEntity.ok()
                .contentType(MediaType.valueOf("video/mp4"))
                .body(response.responseVideo());
    }

    @PostMapping("/audio")
    public ResponseEntity<StreamingResponseBody> requestSttResponse(HttpServletRequest request, @RequestParam("file") MultipartFile file, @RequestParam("roomPath") String roomPath, @RequestParam(value = "chatId", required = false) String chatId) throws IOException {
        ByteArrayResource fileResource = new ByteArrayResource(file.getBytes()) {
            @Override
            public String getFilename() {
                return file.getOriginalFilename();
            }
        };

        String chatIdNonNull = chatId == null ? "" : chatId;
        AvatarResponse response = pipelineService.processAudio(fileResource, roomPath, chatIdNonNull);
        String clientIp = request.getRemoteAddr();
        webSocketHandler.sendToIp(clientIp, response);

        return ResponseEntity.ok()
                .contentType(MediaType.valueOf("video/mp4"))
                .body(response.responseVideo());
    }
}
