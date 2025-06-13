package com.github.avatar.service;

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

    public void saveAvatar(Jwt jwt, MultipartFile voiceAudio, MultipartFile faceImage) throws IOException {
        String userId = jwt.getSubject();
        ttsService.cloneVoice(userId, voiceAudio.getBytes());
        this.videoService.clearFace(userId);
        this.videoService.saveFaceImage(userId, faceImage.getBytes());
    }
}
