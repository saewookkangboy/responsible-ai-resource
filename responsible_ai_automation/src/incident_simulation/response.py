"""
사고 대응 평가기

사고 대응의 효과성을 평가합니다.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ResponsePhase(Enum):
    """대응 단계"""
    DETECTION = "detection"
    TRIAGE = "triage"
    CONTAINMENT = "containment"
    ERADICATION = "eradication"
    RECOVERY = "recovery"
    POST_INCIDENT = "post_incident"


class ResponseQuality(Enum):
    """대응 품질"""
    EXCELLENT = "excellent"
    GOOD = "good"
    ACCEPTABLE = "acceptable"
    POOR = "poor"
    FAILED = "failed"


@dataclass
class PhaseEvaluation:
    """단계별 평가"""
    phase: ResponsePhase
    duration_seconds: float
    sla_met: bool
    actions_taken: List[str]
    issues_found: List[str]
    score: float  # 0-100
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "phase": self.phase.value,
            "duration_seconds": self.duration_seconds,
            "sla_met": self.sla_met,
            "actions_taken": self.actions_taken,
            "issues_found": self.issues_found,
            "score": self.score
        }


@dataclass
class ResponseReport:
    """대응 리포트"""
    report_id: str
    simulation_id: str
    timestamp: datetime
    scenario_name: str
    overall_quality: ResponseQuality
    overall_score: float
    phase_evaluations: List[PhaseEvaluation]
    communication_score: float
    documentation_score: float
    process_adherence_score: float
    team_coordination_score: float
    strengths: List[str]
    weaknesses: List[str]
    action_items: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "report_id": self.report_id,
            "simulation_id": self.simulation_id,
            "timestamp": self.timestamp.isoformat(),
            "scenario_name": self.scenario_name,
            "overall_quality": self.overall_quality.value,
            "overall_score": self.overall_score,
            "phase_evaluations": [p.to_dict() for p in self.phase_evaluations],
            "communication_score": self.communication_score,
            "documentation_score": self.documentation_score,
            "process_adherence_score": self.process_adherence_score,
            "team_coordination_score": self.team_coordination_score,
            "strengths": self.strengths,
            "weaknesses": self.weaknesses,
            "action_items": self.action_items
        }
    
    def to_markdown(self) -> str:
        """마크다운 리포트"""
        quality_emoji = {
            ResponseQuality.EXCELLENT: "🌟",
            ResponseQuality.GOOD: "✅",
            ResponseQuality.ACCEPTABLE: "🟡",
            ResponseQuality.POOR: "🟠",
            ResponseQuality.FAILED: "❌"
        }.get(self.overall_quality, "⚪")
        
        md = f"""# 사고 대응 평가 리포트

**리포트 ID**: {self.report_id}  
**시뮬레이션 ID**: {self.simulation_id}  
**시나리오**: {self.scenario_name}  
**평가 시간**: {self.timestamp}

## 종합 평가

| 항목 | 점수 |
|------|------|
| 전체 점수 | {self.overall_score:.1f}/100 {quality_emoji} |
| 커뮤니케이션 | {self.communication_score:.1f}/100 |
| 문서화 | {self.documentation_score:.1f}/100 |
| 프로세스 준수 | {self.process_adherence_score:.1f}/100 |
| 팀 협업 | {self.team_coordination_score:.1f}/100 |

## 단계별 평가

"""
        for phase_eval in self.phase_evaluations:
            sla_status = "✅" if phase_eval.sla_met else "❌"
            md += f"""### {phase_eval.phase.value.upper()}

- **소요 시간**: {phase_eval.duration_seconds:.0f}초
- **SLA 준수**: {sla_status}
- **점수**: {phase_eval.score:.1f}/100
- **수행 조치**: {', '.join(phase_eval.actions_taken[:3])}...

"""

        md += "## 강점\n\n"
        for strength in self.strengths:
            md += f"- ✅ {strength}\n"
        
        md += "\n## 개선 필요 사항\n\n"
        for weakness in self.weaknesses:
            md += f"- ⚠️ {weakness}\n"
        
        md += "\n## 액션 아이템\n\n"
        for i, item in enumerate(self.action_items, 1):
            md += f"{i}. {item}\n"
        
        return md


class ResponseEvaluator:
    """
    사고 대응 평가기
    
    시뮬레이션된 사고에 대한 대응의 효과성을 평가합니다.
    
    Example:
        >>> evaluator = ResponseEvaluator()
        >>> report = evaluator.evaluate(simulation_result)
        >>> print(report.to_markdown())
    """
    
    # 각 단계별 SLA (초)
    DEFAULT_PHASE_SLA = {
        ResponsePhase.DETECTION: 300,
        ResponsePhase.TRIAGE: 600,
        ResponsePhase.CONTAINMENT: 900,
        ResponsePhase.ERADICATION: 3600,
        ResponsePhase.RECOVERY: 7200,
        ResponsePhase.POST_INCIDENT: 86400
    }
    
    def __init__(self, phase_sla: Optional[Dict[ResponsePhase, float]] = None):
        self.phase_sla = phase_sla or self.DEFAULT_PHASE_SLA
        logger.info("ResponseEvaluator 초기화")
    
    def evaluate(
        self,
        simulation_result: Any,
        response_log: Optional[List[Dict]] = None
    ) -> ResponseReport:
        """
        대응 평가 수행
        
        Args:
            simulation_result: SimulationResult 객체
            response_log: 대응 로그 (선택)
        
        Returns:
            ResponseReport 객체
        """
        import uuid
        
        report_id = str(uuid.uuid4())[:8]
        
        # 단계별 평가
        phase_evaluations = self._evaluate_phases(simulation_result, response_log)
        
        # 각 영역 점수 계산
        communication_score = self._evaluate_communication(simulation_result, response_log)
        documentation_score = self._evaluate_documentation(simulation_result, response_log)
        process_score = self._evaluate_process_adherence(simulation_result, response_log)
        coordination_score = self._evaluate_team_coordination(simulation_result, response_log)
        
        # 전체 점수 계산
        phase_avg = sum(p.score for p in phase_evaluations) / len(phase_evaluations) if phase_evaluations else 0
        overall_score = (
            phase_avg * 0.4 +
            communication_score * 0.15 +
            documentation_score * 0.15 +
            process_score * 0.15 +
            coordination_score * 0.15
        )
        
        # 품질 등급 결정
        overall_quality = self._determine_quality(overall_score)
        
        # 강점 및 약점 식별
        strengths, weaknesses = self._identify_strengths_weaknesses(
            phase_evaluations, communication_score, documentation_score,
            process_score, coordination_score
        )
        
        # 액션 아이템 생성
        action_items = self._generate_action_items(weaknesses, overall_quality)
        
        return ResponseReport(
            report_id=report_id,
            simulation_id=simulation_result.simulation_id,
            timestamp=datetime.now(),
            scenario_name=simulation_result.scenario_name,
            overall_quality=overall_quality,
            overall_score=overall_score,
            phase_evaluations=phase_evaluations,
            communication_score=communication_score,
            documentation_score=documentation_score,
            process_adherence_score=process_score,
            team_coordination_score=coordination_score,
            strengths=strengths,
            weaknesses=weaknesses,
            action_items=action_items
        )
    
    def _evaluate_phases(
        self,
        simulation_result: Any,
        response_log: Optional[List[Dict]]
    ) -> List[PhaseEvaluation]:
        """단계별 평가"""
        evaluations = []
        
        # 시뮬레이션 결과에서 시간 정보 추출
        metrics = simulation_result.metrics
        
        # Detection
        detection_score = 100 if metrics.detection_time_seconds <= self.phase_sla[ResponsePhase.DETECTION] else max(0, 100 - (metrics.detection_time_seconds - self.phase_sla[ResponsePhase.DETECTION]) / 60)
        evaluations.append(PhaseEvaluation(
            phase=ResponsePhase.DETECTION,
            duration_seconds=metrics.detection_time_seconds,
            sla_met=metrics.detection_time_seconds <= self.phase_sla[ResponsePhase.DETECTION],
            actions_taken=["모니터링 알림 확인", "초기 분석", "에스컬레이션"],
            issues_found=["탐지 지연" if metrics.detection_time_seconds > 300 else "없음"],
            score=detection_score
        ))
        
        # Containment (Response)
        response_score = 100 if metrics.response_time_seconds <= self.phase_sla[ResponsePhase.CONTAINMENT] else max(0, 100 - (metrics.response_time_seconds - self.phase_sla[ResponsePhase.CONTAINMENT]) / 60)
        evaluations.append(PhaseEvaluation(
            phase=ResponsePhase.CONTAINMENT,
            duration_seconds=metrics.response_time_seconds,
            sla_met=metrics.response_time_seconds <= self.phase_sla[ResponsePhase.CONTAINMENT],
            actions_taken=["영향 범위 격리", "트래픽 전환", "폴백 활성화"],
            issues_found=["대응 지연" if metrics.response_time_seconds > 600 else "없음"],
            score=response_score
        ))
        
        # Recovery
        recovery_score = 100 if metrics.recovery_time_seconds <= self.phase_sla[ResponsePhase.RECOVERY] else max(0, 100 - (metrics.recovery_time_seconds - self.phase_sla[ResponsePhase.RECOVERY]) / 360)
        evaluations.append(PhaseEvaluation(
            phase=ResponsePhase.RECOVERY,
            duration_seconds=metrics.recovery_time_seconds,
            sla_met=metrics.recovery_time_seconds <= self.phase_sla[ResponsePhase.RECOVERY],
            actions_taken=["시스템 복구", "검증 테스트", "서비스 재개"],
            issues_found=["복구 지연" if metrics.recovery_time_seconds > 3600 else "없음"],
            score=recovery_score
        ))
        
        return evaluations
    
    def _evaluate_communication(
        self,
        simulation_result: Any,
        response_log: Optional[List[Dict]]
    ) -> float:
        """커뮤니케이션 평가"""
        # 시뮬레이션에서는 기본값 반환
        # 실제 구현에서는 알림 시간, 업데이트 빈도 등 평가
        return 75.0
    
    def _evaluate_documentation(
        self,
        simulation_result: Any,
        response_log: Optional[List[Dict]]
    ) -> float:
        """문서화 평가"""
        # 타임라인 기록 여부, 상세도 등 평가
        timeline_detail = len(simulation_result.timeline)
        return min(timeline_detail * 15, 100)
    
    def _evaluate_process_adherence(
        self,
        simulation_result: Any,
        response_log: Optional[List[Dict]]
    ) -> float:
        """프로세스 준수도 평가"""
        # SLA 준수율 기반
        return 90.0 if simulation_result.passed_sla else 60.0
    
    def _evaluate_team_coordination(
        self,
        simulation_result: Any,
        response_log: Optional[List[Dict]]
    ) -> float:
        """팀 협업 평가"""
        # 시뮬레이션에서는 기본값
        return 70.0
    
    def _determine_quality(self, score: float) -> ResponseQuality:
        """품질 등급 결정"""
        if score >= 90:
            return ResponseQuality.EXCELLENT
        elif score >= 75:
            return ResponseQuality.GOOD
        elif score >= 60:
            return ResponseQuality.ACCEPTABLE
        elif score >= 40:
            return ResponseQuality.POOR
        else:
            return ResponseQuality.FAILED
    
    def _identify_strengths_weaknesses(
        self,
        phase_evals: List[PhaseEvaluation],
        comm_score: float,
        doc_score: float,
        process_score: float,
        coord_score: float
    ) -> tuple:
        """강점/약점 식별"""
        strengths = []
        weaknesses = []
        
        # 단계별 분석
        for phase_eval in phase_evals:
            if phase_eval.sla_met and phase_eval.score >= 80:
                strengths.append(f"{phase_eval.phase.value} 단계 우수 (SLA 준수)")
            elif not phase_eval.sla_met:
                weaknesses.append(f"{phase_eval.phase.value} 단계 SLA 미충족")
        
        # 영역별 분석
        scores = {
            "커뮤니케이션": comm_score,
            "문서화": doc_score,
            "프로세스 준수": process_score,
            "팀 협업": coord_score
        }
        
        for area, score in scores.items():
            if score >= 80:
                strengths.append(f"{area} 우수 ({score:.0f}점)")
            elif score < 60:
                weaknesses.append(f"{area} 개선 필요 ({score:.0f}점)")
        
        return strengths, weaknesses
    
    def _generate_action_items(
        self,
        weaknesses: List[str],
        quality: ResponseQuality
    ) -> List[str]:
        """액션 아이템 생성"""
        items = []
        
        if quality in [ResponseQuality.POOR, ResponseQuality.FAILED]:
            items.append("[긴급] 인시던트 대응 프로세스 전면 재검토 필요")
        
        for weakness in weaknesses:
            if "SLA" in weakness:
                items.append(f"SLA 미충족 원인 분석 및 개선: {weakness}")
            elif "커뮤니케이션" in weakness:
                items.append("커뮤니케이션 채널 및 템플릿 개선")
            elif "문서화" in weakness:
                items.append("인시던트 문서화 가이드라인 수립")
            elif "프로세스" in weakness:
                items.append("대응 프로세스 교육 및 훈련 강화")
            elif "협업" in weakness:
                items.append("크로스 팀 협업 워크숍 실시")
        
        items.append("다음 분기 훈련 일정 수립")
        
        return items
    
    def compare_drills(
        self,
        reports: List[ResponseReport]
    ) -> Dict[str, Any]:
        """
        여러 훈련 결과 비교
        
        Args:
            reports: ResponseReport 목록
        
        Returns:
            비교 분석 결과
        """
        if not reports:
            return {}
        
        scores = [r.overall_score for r in reports]
        
        return {
            "total_drills": len(reports),
            "average_score": sum(scores) / len(scores),
            "best_score": max(scores),
            "worst_score": min(scores),
            "trend": "improving" if len(scores) > 1 and scores[-1] > scores[0] else "stable",
            "scores_over_time": [
                {"timestamp": r.timestamp.isoformat(), "score": r.overall_score}
                for r in reports
            ]
        }
