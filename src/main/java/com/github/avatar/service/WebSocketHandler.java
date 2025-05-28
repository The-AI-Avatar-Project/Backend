package com.github.avatar.service;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.datatype.jdk8.Jdk8Module;
import com.github.avatar.dto.AvatarResponse;
import org.springframework.stereotype.Component;
import org.springframework.web.socket.CloseStatus;
import org.springframework.web.socket.TextMessage;
import org.springframework.web.socket.WebSocketSession;
import org.springframework.web.socket.handler.TextWebSocketHandler;

import java.io.IOException;
import java.util.Map;
import java.util.Objects;
import java.util.concurrent.ConcurrentHashMap;

@Component
public class WebSocketHandler extends TextWebSocketHandler {
    private final ObjectMapper objectMapper;

    public WebSocketHandler() {
        this.objectMapper = new ObjectMapper();
        // Needed, because the AvatarResponse contains an Optional
        this.objectMapper.registerModule(new Jdk8Module());
    }

    private final Map<String, WebSocketSession> ipSessionMap = new ConcurrentHashMap<>();

    public void sendToIp(String ip, AvatarResponse message) throws IOException {
        WebSocketSession session = ipSessionMap.get(ip);
        if (session != null && session.isOpen()) {
            session.sendMessage(new TextMessage(objectMapper.writeValueAsString(message)));
        }
    }

    @Override
    public void afterConnectionEstablished(WebSocketSession session) {
        String ip = Objects.requireNonNull(session.getRemoteAddress()).getAddress().getHostAddress();
        ipSessionMap.put(ip, session);
    }

    @Override
    public void afterConnectionClosed(WebSocketSession session, CloseStatus status) {
        String ip = Objects.requireNonNull(session.getRemoteAddress()).getAddress().getHostAddress();
        ipSessionMap.remove(ip);
    }
}

