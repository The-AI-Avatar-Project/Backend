package com.github.avatar.service;

import org.springframework.ai.chat.client.ChatClient;
import org.springframework.ai.chat.client.advisor.MessageChatMemoryAdvisor;
import org.springframework.ai.chat.client.advisor.vectorstore.QuestionAnswerAdvisor;
import org.springframework.ai.chat.memory.ChatMemory;
import org.springframework.ai.chat.prompt.PromptTemplate;
import org.springframework.ai.document.Document;
import org.springframework.ai.template.st.StTemplateRenderer;
import org.springframework.ai.vectorstore.SearchRequest;
import org.springframework.ai.vectorstore.VectorStore;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Map;

@Service
public class LLMService {
    private final ChatClient chatClient;

    public LLMService(ChatClient.Builder chatClientBuilder, ChatMemory chatMemory, VectorStore vectorStore) {
        this.chatClient = chatClientBuilder
                .defaultAdvisors(
                        MessageChatMemoryAdvisor.builder(chatMemory).build(),
                        QuestionAnswerAdvisor.builder(vectorStore).searchRequest(SearchRequest.builder().similarityThreshold(0.6d).build()).promptTemplate(PromptTemplate.builder().renderer(StTemplateRenderer.builder().startDelimiterToken('{').endDelimiterToken('}').build()).template("""
                                {query}
                                
                                Context information is below, surrounded by ---------------------
                                
                                ---------------------
                                {question_answer_context}
                                ---------------------
                                
                                Given the context and provided history information and not prior knowledge,
                                reply to the user comment. If the answer is not in the context, answer the question based on your own knowledge.
                                """).build()).build())
                .build();

        List<Document> documents = List.of(
                new Document("Mathe 1 beginnt um 13 Uhr", Map.of("room", "/2022/SoSe/Arntz/Bildanalyse", "file", "main.pdf")),
                new Document("Programmieren 1 beginnt um 15 Uhr", Map.of("room", "/2022/SoSe/Arntz/Bildanalyse", "file", "main.pdf")),
                new Document("Theoretische Informatik beginnt um 13 Uhr", Map.of("room", "/2022/SoSe/Arntz/Bildanalyse", "file", "main.pdf"))
        );

        vectorStore.add(documents);
    }

    public String generateResponse(String input, String id) {
        ChatClient.CallResponseSpec response = chatClient
                .prompt()
                .user(input)
                .advisors(a -> a.param(ChatMemory.CONVERSATION_ID, id))
                .advisors(a -> a.param(QuestionAnswerAdvisor.FILTER_EXPRESSION, "room == '" + id + "'"))
                .call();

        return response.content().replaceAll("(?s)<think>.*?</think>", "").trim();
    }

}
