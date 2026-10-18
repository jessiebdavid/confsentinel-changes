package org.confsentinel.engine.service;

import org.confsentinel.engine.domain.RuleEntity;
import org.confsentinel.engine.dto.RuleDtos.ActiveRulesResponse;
import org.confsentinel.engine.dto.RuleDtos.EnrichedRuleDto;
import org.confsentinel.engine.dto.RuleDtos.RuleBatchRequest;
import org.confsentinel.engine.dto.RuleDtos.RuleBatchResponse;
import org.confsentinel.engine.dto.RuleDtos.RuleDefinitionDto;
import org.confsentinel.engine.repository.RuleRepository;
import org.confsentinel.engine.repository.ViolationRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Isolation;
import org.springframework.transaction.annotation.Transactional;

import java.time.OffsetDateTime;
import java.util.*;

@Service
public class PolicyVersioningService {

    private final RuleRepository ruleRepository;
    private final ViolationRepository violationRepository;

    public PolicyVersioningService(RuleRepository ruleRepository, ViolationRepository violationRepository) {
        this.ruleRepository = ruleRepository;
        this.violationRepository = violationRepository;
    }

    @Transactional(readOnly = true)
    public ActiveRulesResponse getActiveRules() {
        List<RuleDefinitionDto> list = ruleRepository.findByActiveTrue().stream()
                .map(this::mapEntityToDto)
                .toList();
        return new ActiveRulesResponse("v1", list.size(), list);
    }

    @Transactional(readOnly = true)
    public List<EnrichedRuleDto> getEnrichedRulesCatalog() {
        return ruleRepository.findAll().stream()
                .map(r -> new EnrichedRuleDto(
                        r.getId().toString(),
                        r.getRuleCode(),
                        r.getName(),
                        r.getCategory(),
                        r.getSeverity(),
                        r.getTargetPattern(),
                        r.getKeyPath(),
                        r.getCheckType(),
                        r.getParameter(),
                        r.getMinValue(),
                        r.getMaxValue(),
                        r.getRemediation(),
                        r.getRuleHash(),
                        r.isActive(),
                        violationRepository.countInterceptionsByRuleId(r.getId())
                ))
                .toList();
    }

    @Transactional(isolation = Isolation.READ_COMMITTED)
    public RuleBatchResponse synchronizePolicies(RuleBatchRequest request, boolean prune) {
        List<RuleEntity> allRules = ruleRepository.findAll();
        Map<String, RuleEntity> activeByCode = new HashMap<>();
        Map<UUID, RuleEntity> allById = new HashMap<>();

        for (RuleEntity r : allRules) {
            allById.put(r.getId(), r);
            if (r.isActive()) {
                activeByCode.put(r.getRuleCode(), r);
            }
        }

        int activated = 0;
        int deactivated = 0;
        int unchanged = 0;
        Set<String> incomingCodes = new HashSet<>();

        for (RuleDefinitionDto dto : request.rules()) {
            UUID targetId = UUID.fromString(dto.id());
            incomingCodes.add(dto.ruleCode());

            if (allById.containsKey(targetId)) {
                RuleEntity existing = allById.get(targetId);
                if (existing.isActive() && existing.getRuleHash().equals(dto.ruleHash())) {
                    unchanged++;
                } else {
                    updateEntityFields(existing, dto, true);
                    ruleRepository.save(existing);
                    activated++;
                }
            } else if (activeByCode.containsKey(dto.ruleCode())) {
                RuleEntity old = activeByCode.get(dto.ruleCode());
                old.setActive(false);
                ruleRepository.save(old);

                RuleEntity newEntity = new RuleEntity();
                newEntity.setId(targetId);
                updateEntityFields(newEntity, dto, true);
                ruleRepository.save(newEntity);

                activated++;
                deactivated++;
            } else {
                RuleEntity newEntity = new RuleEntity();
                newEntity.setId(targetId);
                updateEntityFields(newEntity, dto, true);
                ruleRepository.save(newEntity);
                activated++;
            }
        }

        if (prune) {
            List<UUID> toDeactivate = allRules.stream()
                    .filter(RuleEntity::isActive)
                    .filter(r -> !incomingCodes.contains(r.getRuleCode()))
                    .map(RuleEntity::getId)
                    .toList();

            if (!toDeactivate.isEmpty()) {
                ruleRepository.deactivateRulesByIds(toDeactivate);
                deactivated += toDeactivate.size();
            }
        }

        return new RuleBatchResponse("PROCESSED", activated, deactivated, unchanged);
    }

    private void updateEntityFields(RuleEntity entity, RuleDefinitionDto dto, boolean active) {
        entity.setRuleCode(dto.ruleCode());
        entity.setName(dto.name());
        entity.setCategory(dto.category());
        entity.setSeverity(dto.severity());
        entity.setTargetPattern(dto.targetPattern());
        entity.setKeyPath(dto.keyPath());
        entity.setCheckType(dto.checkType());
        entity.setParameter(dto.parameter());
        entity.setMinValue(dto.minValue());
        entity.setMaxValue(dto.maxValue());
        entity.setRemediation(dto.remediation());
        entity.setRuleHash(dto.ruleHash());
        entity.setActive(active);
        entity.setCreatedAt(OffsetDateTime.now());
    }

    private RuleDefinitionDto mapEntityToDto(RuleEntity r) {
        return new RuleDefinitionDto(
                r.getId().toString(),
                r.getRuleCode(),
                r.getName(),
                r.getCategory(),
                r.getSeverity(),
                r.getTargetPattern(),
                r.getKeyPath(),
                r.getCheckType(),
                r.getParameter(),
                r.getMinValue(),
                r.getMaxValue(),
                r.getRemediation(),
                r.getRuleHash()
        );
    }
}