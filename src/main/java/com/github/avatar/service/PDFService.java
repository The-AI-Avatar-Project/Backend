package com.github.avatar.service;

import com.github.avatar.Main;
import org.springframework.ai.document.Document;
import org.springframework.ai.reader.ExtractedTextFormatter;
import org.springframework.ai.reader.pdf.PagePdfDocumentReader;
import org.springframework.ai.reader.pdf.config.PdfDocumentReaderConfig;
import org.springframework.ai.vectorstore.VectorStore;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.Resource;
import org.springframework.core.io.UrlResource;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;

import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.List;

@Service
public class PDFService {
    private final VectorStore vectorStore;

    @Value("${references_path}")
    private String referencesPath;

    public PDFService(final VectorStore vectorStore) {
        this.vectorStore = vectorStore;
    }

    private void savePdfFile(Resource resource, String id) throws IOException {
        byte[] bytes = resource.getContentAsByteArray();
        File folder = new File(referencesPath + id);
        folder.mkdirs();
        Path path = Paths.get(referencesPath + id, resource.getFilename());

        try {
            Files.write(path, bytes);
        } catch (IOException e) {
            Main.LOGGER.error("Error while saving uploaded pdf: ", e);
        }
    }

    private void savePdfVectorDb(Resource resource, String id) {
        PagePdfDocumentReader pdfReader = new PagePdfDocumentReader(resource,
                PdfDocumentReaderConfig.builder()
                        .withPageTopMargin(0)
                        .withPageExtractedTextFormatter(ExtractedTextFormatter.builder()
                                .withNumberOfTopTextLinesToDelete(0)
                                .build())
                        .withPagesPerDocument(1)
                        .build());

        List<Document> docs = pdfReader.read();

        docs.forEach(document -> document.getMetadata().put("room", id));

        vectorStore.add(docs);
    }

    public void savePdf(Resource resource, String id) throws IOException {
        savePdfVectorDb(resource, id);
        savePdfFile(resource, id);
    }

    public Resource getPdf(String path) throws IOException {
        Path filePath = Paths.get(referencesPath).resolve(path).normalize();

        if (!filePath.toFile().exists()) {
            return null;
        }
        return new UrlResource(filePath.toUri());
    }
}
