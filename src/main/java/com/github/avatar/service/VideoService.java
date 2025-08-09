package com.github.avatar.service;

import com.github.avatar.Main;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;

@Service
public class VideoService {
    @Value("${profiles_path}")
    private String profilesPath;

    public void clearFace(String id) {
        Path videoPath = Paths.get(profilesPath + id + "/face.mp4");
        Path imagePath = Paths.get(profilesPath + id + "/face.png");
        Path lipDetectionPath = Paths.get(profilesPath + id + "/lipdetections.npy");
        try {
            Files.deleteIfExists(videoPath);
            Files.deleteIfExists(imagePath);
            Files.deleteIfExists(lipDetectionPath);
        } catch (IOException e) {
            Main.LOGGER.error("Could not delete face files:", e);
        }

    }

    public void saveFaceImage(String id, byte[] faceImage) throws IOException {
        Path imagePath = Paths.get(profilesPath + id + "/face.png");
        imagePath.toFile().getParentFile().mkdirs();
        Files.write(imagePath, faceImage);
    }
}
