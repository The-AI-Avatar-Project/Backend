package com.github.avatar.service;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.ByteArrayResource;
import org.springframework.stereotype.Service;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.web.client.RestClient;

import java.util.HashMap;

@Service
public class STTService {
    @Value("${stt.server.url}")
    private String sttServerUrl;

    private final RestClient restClient;

    public STTService() {
        this.restClient = RestClient.create();
    }


    public String processAudio(ByteArrayResource resource) {
        MultiValueMap<String, Object> parts = new LinkedMultiValueMap<>();
        parts.add("file", resource);

        var responseBody = restClient.post()
                .uri(sttServerUrl)
                .body(parts)
                .retrieve()
                .body(HashMap.class);

        if (responseBody != null && responseBody.containsKey("transcription")) {
            return responseBody.get("transcription").toString().strip();
        } else {
            throw new RuntimeException("Could not get transcription of input");
        }
    }
}
