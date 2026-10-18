package org.confsentinel.engine.service;

import com.fasterxml.jackson.databind.ObjectMapper;
import jakarta.persistence.EntityManager;
import org.confsentinel.engine.domain.EvaluationEntity;
import org.confsentinel.engine.domain.MicroserviceEntity;
import org.confsentinel.engine.domain.RuleEntity;
import org.confsentinel.engine.domain.ViolationEntity;
import org.confsentinel.engine.dto.EvaluationDtos.EvaluationResponse;
import org.confsentinel.engine.dto.EvaluationDtos.EvaluationTelemetryRequest;
import org.confsentinel.engine.dto.EvaluationDtos.ViolationDto;
import org.confsentinel.engine.dto.ReportDtos.EvaluationSummaryDto;
import org.confsentinel.engine.dto.ReportDtos.ViolationDetailDto;
import org.confsentinel.engine.repository.EvaluationRepository;
import org.confsentinel.engine.repository.MicroserviceRepository;
import org.confsentinel.engine.repository.RuleRepository;
import org.confsentinel.engine.repository.ViolationRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Isolation;
import org.springframework.transaction.annotation.Transactional;

import java.time.OffsetDateTime;
import java.util.List;
import java.util.UUID;

@Service
public class EvaluationIngestionService {

    private final MicroserviceRepository microserviceRepository;
    private final RuleRepository ruleRepository;
    private final EvaluationRepository evaluationRepository;
    private final ViolationRepository violationRepository;
    private final EntityManager entityManager;
    private final ObjectMapper objectMapper;

    public EvaluationIngestionService(
            MicroserviceRepository microserviceRepository,
            RuleRepository ruleRepository,
            EvaluationRepository evaluationRepository,
            ViolationRepository violationRepository,
            EntityManager entityManager,
            ObjectMapper objectMapper) {
        this.microserviceRepository = microserviceRepository;
        this.ruleRepository = ruleRepository;
        this.evaluationRepository = evaluationRepository;
        this.violationRepository = violationRepository;
        this.entityManager = entityManager;
        this.objectMapper = objectMapper;
    }

    @Transactional(isolation = Isolation.READ_COMMITTED)
    public EvaluationResponse ingestEvaluation(EvaluationTelemetryRequest req) {
        String slug = req.serviceName().trim().toLowerCase().replaceAll("[^a-z0-9-]", "-").replaceAll("-+", "-");
        String svcId = "svc-" + slug;
        microserviceRepository.upsertMicroserviceNative(svcId, slug, req.serviceName(), "Unassigned");

        // Pre-insert JIT stubs for rules not yet synchronized
        for (ViolationDto v : req.violations()) {
            UUID ruleUuid = UUID.fromString(v.ruleId());
            ruleRepository.insertJitStubRule(
                    ruleUuid,
                    v.ruleCode(),
                    v.ruleDescriptor().name(),
                    v.ruleDescriptor().category(),
                    v.severity(),
                    v.ruleDescriptor().ruleHash()
            );
        }

        entityManager.flush();
        entityManager.clear();

        MicroserviceEntity managedMicroservice = microserviceRepository.getReferenceById(svcId);

        EvaluationEntity eval = new EvaluationEntity();
        eval.setService(managedMicroservice);
        eval.setEnvironment(req.environment());
        eval.setCommitHash(req.commitHash());
        eval.setBranch(req.branch());
        eval.setAuthor(req.author());
        eval.setStatus(req.status());
        eval.setBlockersCount(req.blockersCount());
        eval.setWarningsCount(req.warningsCount());
        eval.setDurationMs(req.durationMs());

        try {
            eval.setDriftSummary(objectMapper.writeValueAsString(req.driftSummary()));
        } catch (Exception e) {
            eval.setDriftSummary("{}");
        }
        eval.setExecutedAt(OffsetDateTime.now());
        EvaluationEntity savedEval = evaluationRepository.save(eval);

        for (ViolationDto v : req.violations()) {
            RuleEntity ruleRef = ruleRepository.getReferenceById(UUID.fromString(v.ruleId()));
            ViolationEntity violation = new ViolationEntity();
            violation.setEvaluation(savedEval);
            violation.setRule(ruleRef);
            violation.setFilePath(v.filePath());
            violation.setLineNumber(v.lineNumber());
            violation.setSnippet(v.snippet());
            violation.setRemediation(v.remediation());
            violationRepository.save(violation);
        }

        return new EvaluationResponse(savedEval.getId().toString(), "RECORDED", savedEval.getExecutedAt().toString());
    }

    @Transactional(readOnly = true)
    public List<EvaluationSummaryDto> getRecentEvaluations() {
        return evaluationRepository.findTop50ByOrderByExecutedAtDesc().stream()
                .map(e -> new EvaluationSummaryDto(
                        e.getId().toString(),
                        e.getService().getName(),
                        e.getEnvironment(),
                        e.getCommitHash(),
                        e.getAuthor(),
                        e.getStatus(),
                        e.getBlockersCount(),
                        e.getWarningsCount(),
                        e.getExecutedAt().toString(),
                        e.getViolations().stream()
                                .map(v -> new ViolationDetailDto(
                                        v.getRule().getId().toString(),
                                        v.getRule().getRuleCode(),
                                        v.getRule().getSeverity(),
                                        v.getFilePath(),
                                        v.getLineNumber(),
                                        v.getSnippet(),
                                        v.getRemediation()
                                ))
                                .toList()
                ))
                .toList();
    }
}