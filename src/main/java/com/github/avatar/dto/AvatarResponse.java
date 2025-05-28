package com.github.avatar.dto;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import org.springframework.web.servlet.mvc.method.annotation.StreamingResponseBody;

import java.util.Optional;

@JsonIgnoreProperties(value = { "responseVideo" })
public record AvatarResponse(String responseText, StreamingResponseBody responseVideo, Optional<String> requestText) {

}
