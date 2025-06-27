package com.github.avatar.dto;

import java.util.List;

public record LLMResponseDTO(String response, List<String> references) {
}
