package com.github.avatar.service;

import com.github.avatar.Main;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.*;
import org.springframework.stereotype.Service;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.web.client.RestTemplate;

import java.io.File;
import java.io.IOException;
import java.net.URI;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

@Service
public class TTSService {
    @Value("${tts.server.url}")
    private String ttsServerUrl;

    @Value("${video.server.url}")
    private String videoServerUrl;

    @Value("${output_path}")
    private String outputPath;

    public String processText(String text, String id, String language) throws IOException, InterruptedException {
        Map<String, Object> ttsRequest = new HashMap<>();
        ttsRequest.put("speaker_name", id);
        ttsRequest.put("language", language);
        ttsRequest.put("text", text);

        RestTemplate client = new RestTemplate();
        ResponseEntity<Map> ttsResponse = client.postForEntity(URI.create(ttsServerUrl), ttsRequest, Map.class);

        if (!ttsResponse.getStatusCode().is2xxSuccessful() || !ttsResponse.hasBody() || !ttsResponse.getBody().containsKey("uuid")) {
            Main.LOGGER.error("Tts response code unsuccessful: {}", ttsResponse.getStatusCode());
            return null;
        }

        String uuid = (String) ttsResponse.getBody().get("uuid");

        String chunkPath = outputPath + uuid + "/0001p.wav";

        File chunkFile = new File(Paths.get(chunkPath).normalize().toFile().getAbsolutePath());
        long start = System.currentTimeMillis();
        while (!chunkFile.exists()) {
            Thread.sleep(500);
            if (System.currentTimeMillis() - start > 15000) {
                Main.LOGGER.error("Timeout waiting for the first audio chunk.");
                return null;
            }
        }

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_FORM_URLENCODED);

        MultiValueMap<String, String> formData = new LinkedMultiValueMap<>();
        formData.add("professor", id);
        formData.add("uuid", uuid);

        ResponseEntity<String> wav2lipResponse = client.postForEntity(URI.create(videoServerUrl), new HttpEntity<>(formData, headers), String.class);

        if (!wav2lipResponse.getStatusCode().is2xxSuccessful()) {
            Main.LOGGER.error("Wav2Lip failed.");
            return null;
        }

        return uuid;
    }

    public void cloneVoice(String id, byte[] voiceRecording) throws IOException {
        Path audioFile = Paths.get("./share/profiles/" + id + "/cloned_voice.wav");
        audioFile.toFile().getParentFile().mkdirs();
        Files.write(audioFile, voiceRecording);
    }
}
