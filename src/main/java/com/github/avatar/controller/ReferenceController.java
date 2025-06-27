package com.github.avatar.controller;

import com.github.avatar.Main;
import com.github.avatar.service.PipelineService;
import jakarta.servlet.http.HttpServletRequest;
import org.springframework.core.io.Resource;
import org.springframework.core.io.UrlResource;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.oauth2.jwt.Jwt;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.net.MalformedURLException;
import java.nio.file.Path;
import java.nio.file.Paths;

@RestController
@RequestMapping("/references")
public class ReferenceController {
    private final PipelineService pipelineService;

    public ReferenceController(PipelineService pipelineService) {
        this.pipelineService = pipelineService;
    }

    @PostMapping("/upload")
    public ResponseEntity<Void> uploadPdf(@AuthenticationPrincipal Jwt jwt, @RequestParam("file") MultipartFile file, @RequestParam("roomPath") String roomPath) throws IOException {
        if (roomPath != null && !roomPath.isEmpty()) {
            return pipelineService.savePdf(jwt, file.getResource(), roomPath);
        } else {
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED).build();
        }
    }

    @RequestMapping(value = "/get/**", method = RequestMethod.GET)
    public ResponseEntity<Resource> downloadPdf(@AuthenticationPrincipal Jwt jwt, HttpServletRequest request) throws IOException {
        String requestURL = request.getRequestURL().toString();
        String path = requestURL.split("/get/")[1];
        try {
            return pipelineService.getPdf(jwt, path);
        } catch (MalformedURLException e) {
            return ResponseEntity.badRequest().build();
        }
    }


}
