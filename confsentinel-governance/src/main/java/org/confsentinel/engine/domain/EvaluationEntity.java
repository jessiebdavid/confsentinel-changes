package org.confsentinel.engine.domain;

import jakarta.persistence.*;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.type.SqlTypes;

import java.time.OffsetDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

@Entity
@Table(name = "evaluations")
public class EvaluationEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.AUTO)
    private UUID id;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "service_id", nullable = false)
    private MicroserviceEntity service;

    @Column(nullable = false, length = 32)
    private String environment;

    @Column(name = "commit_hash", nullable = false, length = 64)
    private String commitHash;

    @Column(nullable = false, length = 128)
    private String branch;

    @Column(nullable = false, length = 128)
    private String author;

    @Column(nullable = false, length = 16)
    private String status;

    @Column(name = "blockers_count", nullable = false)
    private int blockersCount;

    @Column(name = "warnings_count", nullable = false)
    private int warningsCount;

    @Column(name = "duration_ms", nullable = false)
    private int durationMs;

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "drift_summary", columnDefinition = "jsonb")
    private String driftSummary;

    @Column(name = "executed_at", nullable = false, updatable = false)
    private OffsetDateTime executedAt;

    @OneToMany(mappedBy = "evaluation", cascade = CascadeType.ALL, orphanRemoval = true)
    private List<ViolationEntity> violations = new ArrayList<>();

    public EvaluationEntity() {}

    public UUID getId() {
        return id;
    }

    public void setId(UUID id) {
        this.id = id;
    }

    public MicroserviceEntity getService() {
        return service;
    }

    public void setService(MicroserviceEntity service) {
        this.service = service;
    }

    public String getEnvironment() {
        return environment;
    }

    public void setEnvironment(String environment) {
        this.environment = environment;
    }

    public String getCommitHash() {
        return commitHash;
    }

    public void setCommitHash(String commitHash) {
        this.commitHash = commitHash;
    }

    public String getBranch() {
        return branch;
    }

    public void setBranch(String branch) {
        this.branch = branch;
    }

    public String getAuthor() {
        return author;
    }

    public void setAuthor(String author) {
        this.author = author;
    }

    public String getStatus() {
        return status;
    }

    public void setStatus(String status) {
        this.status = status;
    }

    public int getBlockersCount() {
        return blockersCount;
    }

    public void setBlockersCount(int blockersCount) {
        this.blockersCount = blockersCount;
    }

    public int getWarningsCount() {
        return warningsCount;
    }

    public void setWarningsCount(int warningsCount) {
        this.warningsCount = warningsCount;
    }

    public int getDurationMs() {
        return durationMs;
    }

    public void setDurationMs(int durationMs) {
        this.durationMs = durationMs;
    }

    public String getDriftSummary() {
        return driftSummary;
    }

    public void setDriftSummary(String driftSummary) {
        this.driftSummary = driftSummary;
    }

    public OffsetDateTime getExecutedAt() {
        return executedAt;
    }

    public void setExecutedAt(OffsetDateTime executedAt) {
        this.executedAt = executedAt;
    }

    public List<ViolationEntity> getViolations() {
        return violations;
    }

    public void setViolations(List<ViolationEntity> violations) {
        this.violations = violations;
    }
}