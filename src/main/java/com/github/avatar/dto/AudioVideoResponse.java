package com.github.avatar.dto;

import java.util.Optional;

public record AudioVideoResponse(String responseText, byte[] responseAudio, Optional<String> requestText) {

}
