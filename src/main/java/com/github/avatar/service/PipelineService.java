package com.github.avatar.service;

import com.github.avatar.Main;
import com.github.avatar.dto.AvatarResponse;
import org.springframework.core.io.ByteArrayResource;
import org.springframework.core.io.Resource;
import org.springframework.stereotype.Service;

import java.util.Optional;

@Service
public class PipelineService {
    private final LLMService llmService;
    private final STTService sttService;
    private final TTSService ttsService;
    private final PDFService pdfService;
    private final VideoService videoService;

    public PipelineService(LLMService llmService, STTService sttService, TTSService ttsService, PDFService pdfService, VideoService videoService) {
        this.llmService = llmService;
        this.sttService = sttService;
        this.ttsService = ttsService;
        this.pdfService = pdfService;
        this.videoService = videoService;
    }

    public AvatarResponse processText(String input, String id) {
        String textResponse = llmService.generateResponse(input, id);
        byte[] audioBytes = ttsService.processText(textResponse);
        byte[] videoBytes = videoService.generateVideo(audioBytes);
        return new AvatarResponse(textResponse, videoBytes, Optional.empty());
    }

    public AvatarResponse processAudio(ByteArrayResource input, String id) {
        String requestText = sttService.processAudio(input);
        AvatarResponse response = processText(requestText, id);
        return new AvatarResponse(response.responseText(), response.responseVideo(), Optional.of(requestText));
    }

    public void savePdf(Resource file, String id) {
        pdfService.savePdf(file, id);
    }
}
