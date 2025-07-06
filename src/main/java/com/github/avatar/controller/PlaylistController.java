package com.github.avatar.controller;

import com.github.avatar.Main;
import jakarta.websocket.OnClose;
import jakarta.websocket.OnError;
import jakarta.websocket.OnOpen;
import jakarta.websocket.Session;
import jakarta.websocket.server.PathParam;
import jakarta.websocket.server.ServerEndpoint;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;

@ServerEndpoint("/ws/{uuid}")
@Component
public class PlaylistController {
    @Value("${output_path}")
    private String outputPath;

    private static final Map<String, Set<Session>> activeConnections = new ConcurrentHashMap<>();
    private static final Map<String, Long> lastModifiedTimes = new ConcurrentHashMap<>();


    @OnOpen
    public void onOpen(Session session, @PathParam("uuid") String uuid) {
        activeConnections.computeIfAbsent(uuid, k -> ConcurrentHashMap.newKeySet()).add(session);
    }

    @OnClose
    public void onClose(Session session, @PathParam("uuid") String uuid) {
        Set<Session> sessions = activeConnections.get(uuid);
        if (sessions != null) {
            sessions.remove(session);
        }
    }

    @OnError
    public void onError(Session session, Throwable throwable, @PathParam("uuid") String uuid) {
        onClose(session, uuid);
    }

    @Scheduled(fixedDelay = 500)
    public void notifyUpdates() {
        for (Map.Entry<String, Set<Session>> entry : activeConnections.entrySet()) {
            String uuid = entry.getKey();
            Path m3u8Path = Paths.get(outputPath, uuid, "video", "playlist.m3u8");
            if (Files.exists(m3u8Path)) {
                try {
                    long mtime = Files.getLastModifiedTime(m3u8Path).toMillis();
                    long lastMtime = lastModifiedTimes.getOrDefault(uuid, 0L);

                    if (mtime > lastMtime) {
                        lastModifiedTimes.put(uuid, mtime);
                        Set<Session> sessions = entry.getValue();

                        for (Session session : sessions) {
                            try {
                                session.getBasicRemote().sendText("update");
                            } catch (IOException e) {
                                try {
                                    session.close();
                                } catch (IOException ex) {
                                    // ignore
                                }
                            }
                        }
                        System.out.println("[ws] Playlist updated, sent 'update' to clients (" + uuid + ")");
                    }
                } catch (IOException e) {
                    // ignore
                }
            }
        }
    }

}
