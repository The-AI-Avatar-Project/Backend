package com.github.avatar.service;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.buffer.DataBufferUtils;
import org.springframework.http.MediaType;
import org.springframework.http.client.reactive.ReactorClientHttpConnector;
import org.springframework.stereotype.Service;
import org.springframework.web.reactive.function.client.WebClient;
import org.springframework.web.servlet.mvc.method.annotation.StreamingResponseBody;

import org.springframework.core.io.buffer.DataBuffer;
import reactor.netty.http.HttpProtocol;
import reactor.netty.http.client.HttpClient;

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
        // The video backend is built using Uvicorn.
        // Uvicorn does not support http2 which WebClient uses by default.
        HttpClient httpClient = HttpClient.create().protocol(HttpProtocol.HTTP11);

        this.webClient = WebClient.builder()
                .clientConnector(new ReactorClientHttpConnector(httpClient))
                .build();
    }

    private void saveAudio(byte[] audioBytes, String fileName) throws IOException{
        Path audioFile = Paths.get("./share/transfer/" + fileName);
        audioFile.toFile().getParentFile().mkdirs();
        Files.createFile(audioFile);
        Files.write(audioFile, audioBytes);
    }

    private StreamingResponseBody requestVideo(String audioName, String id) {
        Map<String, Object> payload = new HashMap<>();
        payload.put("audio_name", audioName);
        payload.put("professor_id", id);

        return outputStream -> {
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
                        } finally {
                            DataBufferUtils.release(dataBuffer);
                        }
                    })
                    .doOnError(Throwable::printStackTrace)
                    .blockLast();
            Files.delete(Paths.get("./share/transfer/" + audioName));
        };
    }

    public StreamingResponseBody generateVideo(byte[] audio, String id) throws IOException {
        String filename = System.currentTimeMillis()+".mp3";
        saveAudio(audio, filename);
        return requestVideo(filename, id);
    }
}
