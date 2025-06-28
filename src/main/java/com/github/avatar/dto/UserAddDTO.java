package com.github.avatar.dto;

import java.util.List;

public record UserAddDTO (List<String> userIds, String groupId) {
}
