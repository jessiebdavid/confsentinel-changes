package org.confsentinel.engine.repository;

import org.confsentinel.engine.domain.RuleEntity;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

@Repository
public interface RuleRepository extends JpaRepository<RuleEntity, UUID> {

    List<RuleEntity> findByActiveTrue();

    Optional<RuleEntity> findByRuleCodeAndActiveTrue(String ruleCode);

    @Modifying(clearAutomatically = true)
    @Query("UPDATE RuleEntity r SET r.active = false WHERE r.id IN :ids")
    void deactivateRulesByIds(@Param("ids") List<UUID> ids);

    @Modifying(clearAutomatically = true)
    @Query(value = """
        INSERT INTO rules (
            id, rule_code, name, category, severity, target_pattern, 
            key_path, check_type, remediation, rule_hash, active, created_at
        ) VALUES (
            :id, :ruleCode, :name, :category, :severity, 'UNKNOWN', 
            'UNKNOWN', 'UNKNOWN', 'Auto-registered JIT stub.', :ruleHash, FALSE, CURRENT_TIMESTAMP
        ) ON CONFLICT (id) DO NOTHING
        """, nativeQuery = true)
    void insertJitStubRule(
        @Param("id") UUID id,
        @Param("ruleCode") String ruleCode,
        @Param("name") String name,
        @Param("category") String category,
        @Param("severity") String severity,
        @Param("ruleHash") String ruleHash
    );
}