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
import org.springframework.web.reactive.function.client.WebClient;
import org.springframework.web.servlet.mvc.method.annotation.StreamingResponseBody;

import org.springframework.core.io.buffer.DataBuffer;
import java.io.IOException;
import java.nio.channels.Channels;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.HashMap;
import java.util.Map;

@Service
public class VideoService {
    @Value("${video.server.url}")
    private String videoGenerationServerUrl;
    private final WebClient webClient;

    public VideoService() {
        this.webClient = WebClient.create();
    }

    private void saveAudio(byte[] audioBytes, String fileName) throws IOException{
        Path audioFile = Paths.get("./share/" + fileName);
        audioFile.toFile().getParentFile().mkdirs();
        Files.createFile(audioFile);
        Files.write(audioFile, audioBytes);
    }

    private StreamingResponseBody requestVideo(String audioName) {
        Map<String, Object> payload = new HashMap<>();
        payload.put("file_name", audioName);

        StreamingResponseBody body = outputStream -> {
            webClient.post()
                    .uri(videoGenerationServerUrl)
                    .contentType(MediaType.APPLICATION_JSON)
                    .accept(MediaType.valueOf("video/mp4"))
                    .bodyValue(payload)
                    .retrieve()
                    .bodyToFlux(DataBuffer.class)
                    .doOnNext(dataBuffer -> {
                        try {
                            Channels.newChannel(outputStream).write(dataBuffer.asByteBuffer());
                            outputStream.flush();
                        } catch (IOException e) {
                            throw new RuntimeException(e);
                        }
                    })
                    .doOnError(Throwable::printStackTrace)
                    .blockLast(); // block until complete to keep the stream open
        };

        return body;
    }

    public StreamingResponseBody generateVideo(byte[] audio) throws IOException {
        String filename = System.currentTimeMillis()+".mp3";
        saveAudio(audio, filename);
        StreamingResponseBody videoBody = requestVideo(filename);
        Files.delete(Paths.get("./share/" + filename));
        return videoBody;
    }
}
