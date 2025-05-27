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

@RestController
@RequestMapping("/ai")
public class AiController {
    private final PipelineService pipelineService;
    private final WebSocketHandler webSocketHandler;

    public AiController(PipelineService pipelineService, WebSocketHandler webSocketHandler) {
        this.pipelineService = pipelineService;
        this.webSocketHandler = webSocketHandler;
    }

    @PostMapping(value = {"/text/{id}", "/text"})
    public ResponseEntity<StreamingResponseBody> requestLlmResponse(HttpServletRequest request, @RequestBody String input, @PathVariable(required = false) String id) throws IOException {
        if (id == null || id.isEmpty()) {
            id = "0";
        }

        AvatarResponse response = pipelineService.processText(input, id);
        String clientIp = request.getRemoteAddr();
        webSocketHandler.sendToIp(clientIp, response.responseText());

        return ResponseEntity.ok()
                .contentType(MediaType.valueOf("video/mp4"))
                .body(response.responseVideo());
    }

    @PostMapping(value = {"/audio/{id}", "/audio"})
    public ResponseEntity<StreamingResponseBody> requestSttResponse(HttpServletRequest request, @RequestParam("file") MultipartFile file, @PathVariable(required = false) String id) throws IOException {
        if (id == null || id.isEmpty()) {
            id = "0";
        }
        ByteArrayResource fileResource = new ByteArrayResource(file.getBytes()) {
            @Override
            public String getFilename() {
                return file.getOriginalFilename();
            }
        };

        AvatarResponse response = pipelineService.processAudio(fileResource, id);
        String clientIp = request.getRemoteAddr();
        webSocketHandler.sendToIp(clientIp, response.responseText());

        return ResponseEntity.ok()
                .contentType(MediaType.valueOf("video/mp4"))
                .body(response.responseVideo());
    }

    @PostMapping(value = {"/upload/{id}", "/upload"})
    public void uploadPdf(@RequestParam("file") MultipartFile file, @PathVariable(required = false) String id) {
        if (id == null || id.isEmpty()) {
            id = "0";
        }

        pipelineService.savePdf(file.getResource(), id);
    }
}
