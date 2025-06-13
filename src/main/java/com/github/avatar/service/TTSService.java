package com.github.avatar.service;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.HashMap;
import java.util.Map;

@Service
public class TTSService {
    @Value("${tts.server.url}")
    private String ttsServerUrl;

    public byte[] processText(String text, String id, String language) throws IOException {
        // RestClient did not work for some reason
        RestTemplate restTemplate = new RestTemplate();
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);

        Map<String, String> body = new HashMap<>();
        body.put("text", text);
        body.put("language", language);
        body.put("id", id);

        HttpEntity<Map<String, String>> requestEntity = new HttpEntity<>(body, headers);
        ResponseEntity<String> response = restTemplate.postForEntity(ttsServerUrl, requestEntity, String.class);
        String fileName = response.getBody().replace("\"", "");
        byte[] audio = Files.readAllBytes(Path.of("./share/transfer/" + fileName));
        Files.delete(Path.of("./share/transfer/" + fileName));
        return audio;
    }

    public void cloneVoice(String id, byte[] voiceRecording) throws IOException {
        Path audioFile = Paths.get("./share/profiles/" + id + "/voice.mp3");
        audioFile.toFile().getParentFile().mkdirs();
        Files.write(audioFile, voiceRecording);
    }
}
