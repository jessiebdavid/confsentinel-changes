package org.confsentinel.engine.repository;

import org.confsentinel.engine.domain.ViolationEntity;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.UUID;

@Repository
public interface ViolationRepository extends JpaRepository<ViolationEntity, UUID> {

    @Query("""
        SELECT COUNT(DISTINCT v.evaluation.id) 
        FROM ViolationEntity v 
        WHERE v.rule.id = :ruleId AND v.evaluation.status = 'FAILED'
    """)
    long countInterceptionsByRuleId(@Param("ruleId") UUID ruleId);
}