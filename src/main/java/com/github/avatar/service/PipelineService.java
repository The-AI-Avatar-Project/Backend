package com.github.avatar.service;

import com.github.avatar.dto.AvatarResponse;
import org.springframework.core.io.ByteArrayResource;
import org.springframework.core.io.Resource;
import org.springframework.stereotype.Service;
import org.springframework.web.servlet.mvc.method.annotation.StreamingResponseBody;

import java.io.IOException;
import java.util.Optional;

@Service
public class PipelineService {
    private final LLMService llmService;
    private final STTService sttService;
    private final TTSService ttsService;
    private final PDFService pdfService;
    private final VideoService videoService;
    private final KeycloakService keycloakService;

    public PipelineService(LLMService llmService, STTService sttService, TTSService ttsService, PDFService pdfService, VideoService videoService, KeycloakService keycloakService) {
        this.llmService = llmService;
        this.sttService = sttService;
        this.ttsService = ttsService;
        this.pdfService = pdfService;
        this.videoService = videoService;
        this.keycloakService = keycloakService;
    }

    public AvatarResponse processText(String input, String roomPath, String chatId) throws IOException {
        String textResponse = llmService.generateResponse(input, roomPath);
        String ownerId = keycloakService.getGroupOwnerId(roomPath);
        byte[] audioBytes = ttsService.processText(textResponse, ownerId, "de");
        StreamingResponseBody videoBody = videoService.generateVideo(audioBytes, ownerId);
        return new AvatarResponse(textResponse, videoBody, Optional.empty());
    }

    public AvatarResponse processAudio(ByteArrayResource input, String roomId, String chatId) throws IOException {
        String requestText = sttService.processAudio(input);
        AvatarResponse response = processText(requestText, roomId, chatId);
        return new AvatarResponse(response.responseText(), response.responseVideo(), Optional.of(requestText));
    }

    public void savePdf(Resource file, String id) {
        pdfService.savePdf(file, id);
    }
}
