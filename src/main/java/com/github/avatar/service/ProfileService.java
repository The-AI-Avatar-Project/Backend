package com.github.avatar.service;

import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.Objects;

@Service
public class ProfileService {

    private final Path baseDir = Paths.get("./profile");

    public void saveFiles(String keycloakUserId, MultipartFile[] files) throws IOException {
        Path userDir = baseDir.resolve(keycloakUserId);

        if (!Files.exists(userDir)) {
            Files.createDirectories(userDir);
        }

        for (MultipartFile file : files) {
            Path filePath = userDir.resolve(Objects.requireNonNull(file.getOriginalFilename()));
            Files.write(filePath, file.getBytes());
        }
    }
}