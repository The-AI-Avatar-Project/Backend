package com.github.avatar.dto;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;

import java.util.Optional;

@JsonIgnoreProperties(value = { "responseVideo" })
public record AvatarResponse(LLMResponseDTO responseText, String streamingUUID, Optional<String> requestText) {

}
