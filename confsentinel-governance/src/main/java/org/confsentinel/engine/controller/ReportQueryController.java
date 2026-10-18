package org.confsentinel.engine.controller;

import org.confsentinel.engine.dto.ReportDtos.DashboardSummaryResponse;
import org.confsentinel.engine.service.RollupComplianceService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api/v1/reports")
public class ReportQueryController {

    private final RollupComplianceService rollupService;

    public ReportQueryController(RollupComplianceService rollupService) {
        this.rollupService = rollupService;
    }

    @GetMapping("/summary")
    public ResponseEntity<DashboardSummaryResponse> getSummaryReport() {
        return ResponseEntity.ok(rollupService.getExecutiveSummary());
    }

    @GetMapping("/drift/{serviceId}")
    public ResponseEntity<Map<String, Object>> getServiceDrift(@PathVariable String serviceId) {
        return ResponseEntity.ok(rollupService.getLatestDriftForService(serviceId));
    }
}