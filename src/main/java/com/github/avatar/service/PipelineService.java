package com.github.avatar.service;

import com.github.avatar.dto.AudioVideoResponse;
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

    public PipelineService(LLMService llmService, STTService sttService, TTSService ttsService, PDFService pdfService) {
        this.llmService = llmService;
        this.sttService = sttService;
        this.ttsService = ttsService;
        this.pdfService = pdfService;
    }

    public AudioVideoResponse processText(String input, String id) {
        String textResponse = llmService.generateResponse(input, id);
        byte[] audioBytes = ttsService.processText(textResponse);
        return new AudioVideoResponse(textResponse, audioBytes, Optional.empty());
    }

    public AudioVideoResponse processAudio(ByteArrayResource input, String id) {
        String requestText = sttService.processAudio(input);
        AudioVideoResponse response = processText(requestText, id);
        return new AudioVideoResponse(response.responseText(), response.responseAudio(), Optional.of(requestText));
    }

    public void savePdf(Resource file, String id) {
        pdfService.savePdf(file, id);
    }
}
