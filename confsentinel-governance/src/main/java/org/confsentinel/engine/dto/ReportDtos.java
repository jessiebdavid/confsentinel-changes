package org.confsentinel.engine.dto;

import java.util.List;
import java.util.Map;

public class ReportDtos {

    public record ServiceComplianceMatrixRow(
            String serviceId,
            String serviceName,
            String team,
            Map<String, String> environments,
            String lastEvaluatedAt
    ) {}

    public record DashboardSummaryResponse(
            long totalScans,
            double overallPassRate,
            long activeRulesCount,
            int totalBlockersPrevented,
            List<ServiceComplianceMatrixRow> matrix
    ) {}

    public record EvaluationSummaryDto(
            String id,
            String serviceName,
            String environment,
            String commitHash,
            String author,
            String status,
            int blockersCount,
            int warningsCount,
            String executedAt,
            List<ViolationDetailDto> violations
    ) {}

    public record ViolationDetailDto(
            String ruleId,
            String ruleCode,
            String severity,
            String filePath,
            int lineNumber,
            String snippet,
            String remediation
    ) {}
}