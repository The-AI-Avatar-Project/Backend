package com.github.avatar.service;

import jakarta.annotation.Nullable;
import org.springframework.core.io.ByteArrayResource;
import org.springframework.security.oauth2.jwt.Jwt;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;

@Service
public class AvatarService {
    private final TTSService ttsService;
    private final VideoService videoService;

    public AvatarService(TTSService ttsService, VideoService videoService) {
        this.ttsService = ttsService;
        this.videoService = videoService;
    }

    public void saveAvatar(Jwt jwt, MultipartFile voiceAudio, @Nullable MultipartFile faceVideo, @Nullable MultipartFile faceImage) throws IOException {
        String userId = jwt.getSubject();
        ttsService.cloneVoice(userId, voiceAudio.getBytes());
        if (faceVideo != null) {
            this.videoService.clearFace(userId);
            this.videoService.saveFaceVideo(userId, faceVideo.getBytes());
        }
        if (faceImage != null) {
            this.videoService.clearFace(userId);
            this.videoService.saveFaceImage(userId, faceImage.getBytes());
        }
    }
}
