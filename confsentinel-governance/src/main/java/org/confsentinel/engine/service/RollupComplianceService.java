package org.confsentinel.engine.service;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.confsentinel.engine.domain.EvaluationEntity;
import org.confsentinel.engine.domain.MicroserviceEntity;
import org.confsentinel.engine.dto.ReportDtos.DashboardSummaryResponse;
import org.confsentinel.engine.dto.ReportDtos.ServiceComplianceMatrixRow;
import org.confsentinel.engine.repository.EvaluationRepository;
import org.confsentinel.engine.repository.MicroserviceRepository;
import org.confsentinel.engine.repository.RuleRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.*;

@Service
public class RollupComplianceService {

    private final MicroserviceRepository microserviceRepository;
    private final EvaluationRepository evaluationRepository;
    private final RuleRepository ruleRepository;
    private final ObjectMapper objectMapper;

    public RollupComplianceService(
            MicroserviceRepository microserviceRepository,
            EvaluationRepository evaluationRepository,
            RuleRepository ruleRepository,
            ObjectMapper objectMapper) {
        this.microserviceRepository = microserviceRepository;
        this.evaluationRepository = evaluationRepository;
        this.ruleRepository = ruleRepository;
        this.objectMapper = objectMapper;
    }

    @Transactional(readOnly = true)
    public DashboardSummaryResponse getExecutiveSummary() {
        List<MicroserviceEntity> services = microserviceRepository.findAll();
        List<ServiceComplianceMatrixRow> matrix = new ArrayList<>();

        // Fetch all historical evaluations to guarantee consistent sample space
        List<EvaluationEntity> allEvaluations = evaluationRepository.findAll();
        long totalScans = allEvaluations.size();
        long activeRulesCount = ruleRepository.findByActiveTrue().size();

        // 1. Calculate global historical metrics
        int totalBlockersPrevented = allEvaluations.stream()
                .mapToInt(EvaluationEntity::getBlockersCount)
                .sum();

        // PASSED and WARNINGS count as passing (only FAILED / BLOCKED count as failed)
        long passedScans = allEvaluations.stream()
                .filter(eval -> {
                    String status = eval.getStatus();
                    return "PASSED".equalsIgnoreCase(status) || "WARNINGS".equalsIgnoreCase(status) || "WARNING".equalsIgnoreCase(status);
                })
                .count();

        // Calculate pass rate (100.0% if clean/no scans run yet)
        double passRate = (totalScans == 0) ? 100.0 : ((double) passedScans / totalScans) * 100.0;
        double roundedPassRate = Math.round(passRate * 10.0) / 10.0;

        // 2. Build current environment matrix for services
        List<String> monitoredEnvs = List.of("dev", "staging", "prod");

        for (MicroserviceEntity svc : services) {
            Map<String, String> envStates = new HashMap<>();
            String latestTimestamp = "N/A";

            for (String env : monitoredEnvs) {
                Optional<EvaluationEntity> latestOpt = evaluationRepository.findLatestByServiceAndEnv(svc.getId(), env);
                if (latestOpt.isPresent()) {
                    EvaluationEntity eval = latestOpt.get();
                    // Normalize status string for frontend display
                    envStates.put(env, eval.getStatus());
                    if (eval.getExecutedAt() != null) {
                        latestTimestamp = eval.getExecutedAt().toString();
                    }
                } else {
                    envStates.put(env, "NO_DATA");
                }
            }

            matrix.add(new ServiceComplianceMatrixRow(
                    svc.getId(),
                    svc.getName(),
                    svc.getTeam(),
                    envStates,
                    latestTimestamp
            ));
        }

        return new DashboardSummaryResponse(
                totalScans,
                roundedPassRate,
                activeRulesCount,
                totalBlockersPrevented,
                matrix
        );
    }

    @Transactional(readOnly = true)
    public Map<String, Object> getLatestDriftForService(String serviceId) {
        Optional<EvaluationEntity> latestOpt = evaluationRepository.findLatestByServiceAndEnv(serviceId, "prod");
        if (latestOpt.isEmpty()) {
            latestOpt = evaluationRepository.findLatestByServiceAndEnv(serviceId, "staging");
        }
        if (latestOpt.isEmpty() || latestOpt.get().getDriftSummary() == null) {
            return Map.of("status", "NO_DRIFT_DATA", "unboundBaseKeys", List.of());
        }

        try {
            return objectMapper.readValue(latestOpt.get().getDriftSummary(), new TypeReference<Map<String, Object>>() {});
        } catch (Exception e) {
            return Map.of("status", "PARSE_ERROR", "unboundBaseKeys", List.of());
        }
    }
}