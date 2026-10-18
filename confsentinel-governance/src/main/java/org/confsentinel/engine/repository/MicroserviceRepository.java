package org.confsentinel.engine.repository;

import org.confsentinel.engine.domain.MicroserviceEntity;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.Optional;

@Repository
public interface MicroserviceRepository extends JpaRepository<MicroserviceEntity, String> {

    Optional<MicroserviceEntity> findBySlug(String slug);

    @Modifying(clearAutomatically = true)
    @Query(value = """
        INSERT INTO microservices (id, slug, name, team, created_at, updated_at)
        VALUES (:id, :slug, :name, :team, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        ON CONFLICT (slug) DO UPDATE
        SET updated_at = CURRENT_TIMESTAMP
        """, nativeQuery = true)
    void upsertMicroserviceNative(
        @Param("id") String id,
        @Param("slug") String slug,
        @Param("name") String name,
        @Param("team") String team
    );
}