package com.github.avatar.service;

import com.github.avatar.Main;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.RestTemplate;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.HashMap;
import java.util.Map;

@Service
public class VideoService {
    @Value("${video.server.url}")
    private String videoGenerationServerUrl;

    private void saveAudio(byte[] audioBytes, String fileName) throws IOException{
        Path audioFile = Paths.get("./share/" + fileName);
        audioFile.toFile().getParentFile().mkdirs();
        Files.createFile(audioFile);
        Files.write(audioFile, audioBytes);
    }

    private String requestVideo(String audioName) {
        RestTemplate restTemplate = new RestTemplate();
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);

        Map<String, String> body = new HashMap<>();
        body.put("file_name", audioName);

        HttpEntity<Map<String, String>> requestEntity = new HttpEntity<>(body, headers);
        return restTemplate.postForObject(videoGenerationServerUrl, requestEntity, String.class).replaceAll("\"", "");
    }

    public byte[] generateVideo(byte[] audio) {
        try {
            String filename = System.currentTimeMillis()+".mp3";
            saveAudio(audio, filename);
            String videoName = requestVideo(filename);
            byte[] videoBytes = Files.readAllBytes(Paths.get("./share/" + videoName));
            Files.delete(Paths.get("./share/" + filename));
            Files.delete(Paths.get("./share/" + videoName));
            return videoBytes;
        } catch (IOException e) {
            e.printStackTrace();
            return new byte[0];
        }
    }
}
