package com.github.avatar.service;

import org.springframework.core.io.ByteArrayResource;
import org.springframework.security.oauth2.jwt.Jwt;
import org.springframework.stereotype.Service;

import java.io.IOException;

@Service
public class AvatarService {
    private final TTSService ttsService;

    public AvatarService(TTSService ttsService) {
        this.ttsService = ttsService;
    }

    public void createAvatar(Jwt jwt, ByteArrayResource voiceRecording) throws IOException {
        ttsService.cloneVoice(jwt.getSubject(), voiceRecording);
    }
}
