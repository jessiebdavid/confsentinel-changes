package org.confsentinel.engine.controller;

import jakarta.validation.Valid;
import org.confsentinel.engine.dto.EvaluationDtos.EvaluationResponse;
import org.confsentinel.engine.dto.EvaluationDtos.EvaluationTelemetryRequest;
import org.confsentinel.engine.dto.ReportDtos.EvaluationSummaryDto;
import org.confsentinel.engine.service.EvaluationIngestionService;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/v1/evaluations")
public class EvaluationController {

    private final EvaluationIngestionService evaluationService;

    public EvaluationController(EvaluationIngestionService evaluationService) {
        this.evaluationService = evaluationService;
    }

    @PostMapping
    public ResponseEntity<EvaluationResponse> ingestEvaluation(
            @Valid @RequestBody EvaluationTelemetryRequest request
    ) {
        EvaluationResponse response = evaluationService.ingestEvaluation(request);
        return ResponseEntity.status(HttpStatus.CREATED).body(response);
    }

    @GetMapping
    public ResponseEntity<List<EvaluationSummaryDto>> getRecentEvaluations() {
        return ResponseEntity.ok(evaluationService.getRecentEvaluations());
    }
}