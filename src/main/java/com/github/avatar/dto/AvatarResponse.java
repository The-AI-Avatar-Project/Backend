package com.github.avatar.dto;

import org.springframework.web.servlet.mvc.method.annotation.StreamingResponseBody;

import java.util.Optional;

public record AvatarResponse(String responseText, StreamingResponseBody responseVideo, Optional<String> requestText) {

}
