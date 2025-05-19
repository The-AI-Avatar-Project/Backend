package com.github.avatar.controller;

import com.github.avatar.dto.AvatarResponse;
import com.github.avatar.service.PipelineService;
import org.springframework.core.io.ByteArrayResource;
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

    @PostMapping(value = {"/text/{id}", "/text"})
    public AvatarResponse requestLlmResponse(@RequestBody String request, @PathVariable(required = false) String id) {
        if (id == null || id.isEmpty()) {
            id = "0";
        }
        return pipelineService.processText(request, id);
    }

    @PostMapping(value = {"/audio/{id}", "/audio"})
    public AvatarResponse requestSttResponse(@RequestParam("file") MultipartFile file, @PathVariable(required = false) String id) throws IOException {
        if (id == null || id.isEmpty()) {
            id = "0";
        }
        ByteArrayResource fileResource = new ByteArrayResource(file.getBytes()) {
            @Override
            public String getFilename() {
                return file.getOriginalFilename();
            }
        };

        return pipelineService.processAudio(fileResource, id);
    }

    @PostMapping(value = {"/upload/{id}", "/upload"})
    public void uploadPdf(@RequestParam("file") MultipartFile file, @PathVariable(required = false) String id) {
        if (id == null || id.isEmpty()) {
            id = "0";
        }

        pipelineService.savePdf(file.getResource(), id);
    }
}
