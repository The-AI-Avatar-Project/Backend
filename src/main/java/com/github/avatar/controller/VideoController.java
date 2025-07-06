package com.github.avatar.controller;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.servlet.mvc.method.annotation.StreamingResponseBody;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;

@RestController
public class VideoController {
    @Value("${output_path}")
    private String outputPath;


    @GetMapping("/stream/{uuid}/playlist.m3u8")
    public ResponseEntity<StreamingResponseBody> getPlaylist(@PathVariable String uuid) {
        Path path = Paths.get(outputPath, uuid, "video", "playlist.m3u8");
        if (!Files.exists(path)) {
            return ResponseEntity.status(HttpStatus.NOT_FOUND).body(null);
        }

        StreamingResponseBody stream = outputStream -> Files.copy(path, outputStream);

        return ResponseEntity.ok()
                .header(HttpHeaders.CONTENT_TYPE, "application/vnd.apple.mpegurl")
                .body(stream);
    }

    @RequestMapping(value = "/stream/{uuid}/playlist.m3u8", method = RequestMethod.HEAD)
    public ResponseEntity<Void> headPlaylist(@PathVariable String uuid) throws IOException {
        Path path = Paths.get(outputPath, uuid, "video", "playlist.m3u8");
        if (!Files.exists(path)) {
            return ResponseEntity.status(HttpStatus.NOT_FOUND).build();
        }

        long size = Files.size(path);
        HttpHeaders headers = new HttpHeaders();
        headers.setContentLength(size);
        headers.setContentType(MediaType.valueOf("application/vnd.apple.mpegurl"));

        return new ResponseEntity<>(headers, HttpStatus.OK);
    }

    @GetMapping("/stream/{uuid}/{filename}")
    public ResponseEntity<StreamingResponseBody> getSegment(@PathVariable String uuid, @PathVariable String filename) throws IOException {
        Path path = Paths.get(outputPath, uuid, "video", filename);
        if (!Files.exists(path)) {
            return ResponseEntity.status(HttpStatus.NOT_FOUND).body(null);
        }

        StreamingResponseBody stream = outputStream -> {
            Files.copy(path, outputStream);
        };

        return ResponseEntity.ok()
                .header(HttpHeaders.CONTENT_TYPE, "video/MP2T")
                .body(stream);
    }

}
