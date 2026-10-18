package org.confsentinel.engine.repository;

import org.confsentinel.engine.domain.EvaluationEntity;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

@Repository
public interface EvaluationRepository extends JpaRepository<EvaluationEntity, UUID> {

    @Query(value = """
        SELECT * FROM evaluations e 
        WHERE e.service_id = :serviceId AND e.environment = :env 
        ORDER BY e.executed_at DESC LIMIT 1
        """, nativeQuery = true)
    Optional<EvaluationEntity> findLatestByServiceAndEnv(
        @Param("serviceId") String serviceId,
        @Param("env") String env
    );

    List<EvaluationEntity> findTop50ByOrderByExecutedAtDesc();
}