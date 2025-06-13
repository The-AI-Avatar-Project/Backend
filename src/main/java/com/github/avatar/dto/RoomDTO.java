package com.github.avatar.dto;

import java.util.List;
import java.util.Map;

public record RoomDTO(String path, String name, Map<String, List<String>> attributes) {
}
