package org.confsentinel.engine.dto;

import jakarta.validation.Valid;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Pattern;

import java.math.BigDecimal;
import java.util.List;

public class RuleDtos {

    public record RuleDefinitionDto(
            @NotBlank String id,
            @Pattern(regexp = "^[A-Z]{3,4}-[0-9]{3,4}$") String ruleCode,
            @NotBlank String name,
            @NotBlank String category,
            @NotBlank String severity,
            @NotBlank String targetPattern,
            @NotBlank String keyPath,
            @NotBlank String checkType,
            String parameter,
            BigDecimal minValue,
            BigDecimal maxValue,
            @NotBlank String remediation,
            @NotBlank String ruleHash
    ) {}

    public record EnrichedRuleDto(
            String id,
            String ruleCode,
            String name,
            String category,
            String severity,
            String targetPattern,
            String keyPath,
            String checkType,
            String parameter,
            BigDecimal minValue,
            BigDecimal maxValue,
            String remediation,
            String ruleHash,
            boolean active,
            long interceptionsCount
    ) {}

    public record RuleBatchRequest(
            @NotBlank String batchId,
            @NotBlank String publishedBy,
            @NotNull @Valid List<RuleDefinitionDto> rules
    ) {}

    public record RuleBatchResponse(
            String status,
            int activated,
            int deactivated,
            int unchanged
    ) {}

    public record ActiveRulesResponse(
            String version,
            int count,
            List<RuleDefinitionDto> rules
    ) {}
}