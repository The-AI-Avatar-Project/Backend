package com.github.avatar.dto;

import java.util.Optional;

public record AvatarResponse(String responseText, byte[] responseVideo, Optional<String> requestText) {

}
