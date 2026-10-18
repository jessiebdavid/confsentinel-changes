package org.confsentinel.engine.dto;

import jakarta.validation.Valid;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Pattern;

import java.util.List;

public class EvaluationDtos {

    public record RuleDescriptorDto(
            @NotBlank String ruleHash,
            @NotBlank String name,
            @NotBlank String category
    ) {}

    public record ViolationDto(
            @NotBlank String ruleId,
            @NotBlank String ruleCode,
            @Pattern(regexp = "^(BLOCKER|CRITICAL|WARNING)$") String severity,
            @NotBlank String filePath,
            @Min(1) int lineNumber,
            @NotBlank String snippet,
            @NotBlank String remediation,
            @NotNull @Valid RuleDescriptorDto ruleDescriptor
    ) {}

    public record DriftSummaryDto(
            @NotBlank String baseEnv,
            @NotBlank String targetEnv,
            int baseKeysCount,
            int targetKeysCount,
            List<String> unboundBaseKeys
    ) {}

    public record EvaluationTelemetryRequest(
            @NotBlank String serviceName,
            @NotBlank String environment,
            @NotBlank String commitHash,
            @NotBlank String branch,
            @NotBlank String author,
            int durationMs,
            @Pattern(regexp = "^(PASSED|WARNINGS|FAILED)$") String status,
            int blockersCount,
            int warningsCount,
            @NotNull DriftSummaryDto driftSummary,
            @NotNull @Valid List<ViolationDto> violations
    ) {}

    public record EvaluationResponse(
            String evaluationId,
            String status,
            String recordedAt
    ) {}
}