"""
AI 사고 시뮬레이터

다양한 AI 장애/사고 시나리오를 시뮬레이션합니다.
"""

from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging
import time

logger = logging.getLogger(__name__)


class SimulationStatus(Enum):
    """시뮬레이션 상태"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    ABORTED = "aborted"


class SeverityLevel(Enum):
    """심각도 수준"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class IncidentMetrics:
    """사고 지표"""
    detection_time_seconds: float       # 탐지까지 시간
    response_time_seconds: float        # 대응까지 시간
    recovery_time_seconds: float        # 복구까지 시간
    impact_score: float                 # 영향 점수 (0-100)
    affected_users_percent: float       # 영향 받은 사용자 비율
    data_loss_percent: float            # 데이터 손실 비율
    accuracy_degradation: float         # 정확도 저하
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "detection_time_seconds": self.detection_time_seconds,
            "response_time_seconds": self.response_time_seconds,
            "recovery_time_seconds": self.recovery_time_seconds,
            "impact_score": self.impact_score,
            "affected_users_percent": self.affected_users_percent,
            "data_loss_percent": self.data_loss_percent,
            "accuracy_degradation": self.accuracy_degradation
        }


@dataclass
class TimelineEvent:
    """타임라인 이벤트"""
    timestamp: datetime
    event_type: str
    description: str
    actor: str  # system, human, attacker 등
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "event_type": self.event_type,
            "description": self.description,
            "actor": self.actor
        }


@dataclass
class SimulationResult:
    """시뮬레이션 결과"""
    simulation_id: str
    scenario_name: str
    severity: SeverityLevel
    status: SimulationStatus
    start_time: datetime
    end_time: Optional[datetime]
    metrics: IncidentMetrics
    timeline: List[TimelineEvent]
    lessons_learned: List[str]
    recommendations: List[str]
    passed_sla: bool
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "simulation_id": self.simulation_id,
            "scenario_name": self.scenario_name,
            "severity": self.severity.value,
            "status": self.status.value,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": (self.end_time - self.start_time).total_seconds() if self.end_time else None,
            "metrics": self.metrics.to_dict(),
            "timeline": [e.to_dict() for e in self.timeline],
            "lessons_learned": self.lessons_learned,
            "recommendations": self.recommendations,
            "passed_sla": self.passed_sla
        }
    
    def to_markdown(self) -> str:
        """마크다운 리포트"""
        status_emoji = {
            SimulationStatus.COMPLETED: "✅",
            SimulationStatus.FAILED: "❌",
            SimulationStatus.ABORTED: "⚠️"
        }.get(self.status, "⏳")
        
        sla_status = "✅ 충족" if self.passed_sla else "❌ 미충족"
        
        md = f"""# AI 사고 시뮬레이션 리포트

**시뮬레이션 ID**: {self.simulation_id}  
**시나리오**: {self.scenario_name}  
**심각도**: {self.severity.value}  
**상태**: {status_emoji} {self.status.value}

## 요약

| 지표 | 값 |
|------|-----|
| 탐지 시간 | {self.metrics.detection_time_seconds:.1f}초 |
| 대응 시간 | {self.metrics.response_time_seconds:.1f}초 |
| 복구 시간 | {self.metrics.recovery_time_seconds:.1f}초 |
| 영향 점수 | {self.metrics.impact_score:.1f}/100 |
| 정확도 저하 | {self.metrics.accuracy_degradation:.1%} |
| SLA 준수 | {sla_status} |

## 타임라인

"""
        for event in self.timeline:
            actor_emoji = {"system": "🤖", "human": "👤", "attacker": "☠️"}.get(event.actor, "📌")
            md += f"- **{event.timestamp.strftime('%H:%M:%S')}** {actor_emoji} [{event.event_type}] {event.description}\n"
        
        md += "\n## 교훈\n\n"
        for lesson in self.lessons_learned:
            md += f"- {lesson}\n"
        
        md += "\n## 권고사항\n\n"
        for i, rec in enumerate(self.recommendations, 1):
            md += f"{i}. {rec}\n"
        
        return md


class AIIncidentSimulator:
    """
    AI 사고 시뮬레이터
    
    다양한 AI 장애/사고 시나리오를 시뮬레이션하여 시스템의 탄력성과 
    대응 역량을 테스트합니다.
    
    Example:
        >>> simulator = AIIncidentSimulator()
        >>> result = simulator.simulate(
        ...     scenario="model_drift",
        ...     target_system=my_system,
        ...     severity=SeverityLevel.HIGH
        ... )
        >>> print(result.to_markdown())
    """
    
    # SLA 기준 (초)
    DEFAULT_SLA = {
        SeverityLevel.LOW: {"detection": 3600, "response": 7200, "recovery": 86400},
        SeverityLevel.MEDIUM: {"detection": 1800, "response": 3600, "recovery": 28800},
        SeverityLevel.HIGH: {"detection": 300, "response": 900, "recovery": 7200},
        SeverityLevel.CRITICAL: {"detection": 60, "response": 300, "recovery": 3600},
    }
    
    def __init__(self, sla_config: Optional[Dict] = None):
        self.sla_config = sla_config or self.DEFAULT_SLA
        self._simulation_history: List[SimulationResult] = []
        self._callbacks: Dict[str, List[Callable]] = {
            "on_start": [],
            "on_incident": [],
            "on_detection": [],
            "on_response": [],
            "on_recovery": [],
            "on_complete": []
        }
        logger.info("AIIncidentSimulator 초기화")
    
    def register_callback(
        self,
        event: str,
        callback: Callable
    ):
        """이벤트 콜백 등록"""
        if event in self._callbacks:
            self._callbacks[event].append(callback)
    
    def simulate(
        self,
        scenario: str,
        target_system: Any,
        severity: SeverityLevel = SeverityLevel.MEDIUM,
        duration_seconds: int = 300,
        inject_at_seconds: int = 30
    ) -> SimulationResult:
        """
        사고 시뮬레이션 실행
        
        Args:
            scenario: 시나리오 유형 (model_drift, data_poisoning, adversarial 등)
            target_system: 대상 AI 시스템
            severity: 심각도 수준
            duration_seconds: 시뮬레이션 총 시간
            inject_at_seconds: 사고 주입 시점
        
        Returns:
            SimulationResult 객체
        """
        import uuid
        
        simulation_id = str(uuid.uuid4())[:8]
        start_time = datetime.now()
        timeline = []
        
        logger.info(f"시뮬레이션 시작: {scenario} (severity={severity.value})")
        
        # 시작 이벤트
        timeline.append(TimelineEvent(
            timestamp=start_time,
            event_type="simulation_start",
            description=f"{scenario} 시뮬레이션 시작",
            actor="system"
        ))
        self._trigger_callbacks("on_start", simulation_id, scenario)
        
        # 사고 주입
        incident_time = start_time + timedelta(seconds=inject_at_seconds)
        timeline.append(TimelineEvent(
            timestamp=incident_time,
            event_type="incident_injected",
            description=f"{severity.value} 수준 {scenario} 사고 주입",
            actor="system"
        ))
        self._trigger_callbacks("on_incident", simulation_id, scenario)
        
        # 탐지 시뮬레이션
        detection_delay = self._simulate_detection(scenario, severity)
        detection_time = incident_time + timedelta(seconds=detection_delay)
        timeline.append(TimelineEvent(
            timestamp=detection_time,
            event_type="incident_detected",
            description="모니터링 시스템이 이상 탐지",
            actor="system"
        ))
        self._trigger_callbacks("on_detection", simulation_id, detection_delay)
        
        # 대응 시뮬레이션
        response_delay = self._simulate_response(scenario, severity)
        response_time = detection_time + timedelta(seconds=response_delay)
        timeline.append(TimelineEvent(
            timestamp=response_time,
            event_type="response_initiated",
            description="사고 대응 프로세스 시작",
            actor="human"
        ))
        self._trigger_callbacks("on_response", simulation_id, response_delay)
        
        # 복구 시뮬레이션
        recovery_delay = self._simulate_recovery(scenario, severity)
        recovery_time = response_time + timedelta(seconds=recovery_delay)
        timeline.append(TimelineEvent(
            timestamp=recovery_time,
            event_type="system_recovered",
            description="시스템 정상 복구 완료",
            actor="system"
        ))
        self._trigger_callbacks("on_recovery", simulation_id, recovery_delay)
        
        end_time = datetime.now()
        
        # 지표 계산
        metrics = IncidentMetrics(
            detection_time_seconds=detection_delay,
            response_time_seconds=response_delay,
            recovery_time_seconds=recovery_delay,
            impact_score=self._calculate_impact_score(severity, detection_delay),
            affected_users_percent=self._estimate_affected_users(severity),
            data_loss_percent=0.0 if scenario != "data_poisoning" else 5.0,
            accuracy_degradation=self._estimate_accuracy_degradation(scenario, severity)
        )
        
        # SLA 준수 여부
        sla = self.sla_config[severity]
        passed_sla = (
            detection_delay <= sla["detection"] and
            response_delay <= sla["response"] and
            recovery_delay <= sla["recovery"]
        )
        
        # 교훈 및 권고사항
        lessons = self._generate_lessons(scenario, metrics)
        recommendations = self._generate_recommendations(scenario, metrics, passed_sla)
        
        result = SimulationResult(
            simulation_id=simulation_id,
            scenario_name=scenario,
            severity=severity,
            status=SimulationStatus.COMPLETED,
            start_time=start_time,
            end_time=end_time,
            metrics=metrics,
            timeline=timeline,
            lessons_learned=lessons,
            recommendations=recommendations,
            passed_sla=passed_sla
        )
        
        self._simulation_history.append(result)
        self._trigger_callbacks("on_complete", result)
        
        return result
    
    def _simulate_detection(
        self,
        scenario: str,
        severity: SeverityLevel
    ) -> float:
        """탐지 시간 시뮬레이션"""
        import random
        
        # 기본 탐지 시간 (초)
        base_times = {
            "model_drift": 600,       # 10분
            "data_poisoning": 1800,   # 30분
            "adversarial": 120,       # 2분
            "system_failure": 30,     # 30초
        }
        
        base = base_times.get(scenario, 300)
        
        # 심각도에 따른 조정
        severity_multiplier = {
            SeverityLevel.LOW: 1.5,
            SeverityLevel.MEDIUM: 1.0,
            SeverityLevel.HIGH: 0.7,
            SeverityLevel.CRITICAL: 0.5,
        }
        
        adjusted = base * severity_multiplier[severity]
        
        # 랜덤 변동 추가
        return adjusted * random.uniform(0.8, 1.2)
    
    def _simulate_response(
        self,
        scenario: str,
        severity: SeverityLevel
    ) -> float:
        """대응 시간 시뮬레이션"""
        import random
        
        base_times = {
            "model_drift": 300,
            "data_poisoning": 600,
            "adversarial": 180,
            "system_failure": 120,
        }
        
        base = base_times.get(scenario, 300)
        
        # 심각도가 높을수록 빠른 대응
        severity_multiplier = {
            SeverityLevel.LOW: 2.0,
            SeverityLevel.MEDIUM: 1.0,
            SeverityLevel.HIGH: 0.5,
            SeverityLevel.CRITICAL: 0.25,
        }
        
        return base * severity_multiplier[severity] * random.uniform(0.9, 1.1)
    
    def _simulate_recovery(
        self,
        scenario: str,
        severity: SeverityLevel
    ) -> float:
        """복구 시간 시뮬레이션"""
        import random
        
        base_times = {
            "model_drift": 3600,      # 1시간
            "data_poisoning": 7200,   # 2시간
            "adversarial": 1800,      # 30분
            "system_failure": 900,    # 15분
        }
        
        base = base_times.get(scenario, 3600)
        
        severity_multiplier = {
            SeverityLevel.LOW: 0.5,
            SeverityLevel.MEDIUM: 1.0,
            SeverityLevel.HIGH: 2.0,
            SeverityLevel.CRITICAL: 3.0,
        }
        
        return base * severity_multiplier[severity] * random.uniform(0.85, 1.15)
    
    def _calculate_impact_score(
        self,
        severity: SeverityLevel,
        detection_time: float
    ) -> float:
        """영향 점수 계산"""
        base_scores = {
            SeverityLevel.LOW: 20,
            SeverityLevel.MEDIUM: 40,
            SeverityLevel.HIGH: 60,
            SeverityLevel.CRITICAL: 80,
        }
        
        base = base_scores[severity]
        # 탐지 시간이 길수록 영향 증가
        time_penalty = min(detection_time / 3600 * 10, 20)
        
        return min(base + time_penalty, 100)
    
    def _estimate_affected_users(self, severity: SeverityLevel) -> float:
        """영향 받은 사용자 비율 추정"""
        return {
            SeverityLevel.LOW: 5.0,
            SeverityLevel.MEDIUM: 15.0,
            SeverityLevel.HIGH: 35.0,
            SeverityLevel.CRITICAL: 75.0,
        }[severity]
    
    def _estimate_accuracy_degradation(
        self,
        scenario: str,
        severity: SeverityLevel
    ) -> float:
        """정확도 저하 추정"""
        scenario_base = {
            "model_drift": 0.1,
            "data_poisoning": 0.2,
            "adversarial": 0.15,
            "system_failure": 0.0,
        }
        
        base = scenario_base.get(scenario, 0.1)
        multiplier = {
            SeverityLevel.LOW: 0.5,
            SeverityLevel.MEDIUM: 1.0,
            SeverityLevel.HIGH: 1.5,
            SeverityLevel.CRITICAL: 2.0,
        }[severity]
        
        return min(base * multiplier, 0.5)
    
    def _generate_lessons(
        self,
        scenario: str,
        metrics: IncidentMetrics
    ) -> List[str]:
        """교훈 생성"""
        lessons = []
        
        if metrics.detection_time_seconds > 600:
            lessons.append("탐지 시간이 10분을 초과했습니다. 모니터링 민감도 조정이 필요합니다.")
        
        if metrics.response_time_seconds > 300:
            lessons.append("대응 시간이 5분을 초과했습니다. 에스컬레이션 프로세스를 개선하세요.")
        
        scenario_lessons = {
            "model_drift": "정기적인 모델 성능 모니터링과 자동 재학습 파이프라인이 중요합니다.",
            "data_poisoning": "데이터 입력 검증과 이상치 탐지가 필수적입니다.",
            "adversarial": "실시간 적대적 입력 탐지 메커니즘이 필요합니다.",
            "system_failure": "고가용성 아키텍처와 자동 장애 조치가 효과적입니다."
        }
        
        if scenario in scenario_lessons:
            lessons.append(scenario_lessons[scenario])
        
        return lessons
    
    def _generate_recommendations(
        self,
        scenario: str,
        metrics: IncidentMetrics,
        passed_sla: bool
    ) -> List[str]:
        """권고사항 생성"""
        recommendations = []
        
        if not passed_sla:
            recommendations.append("[긴급] SLA 미충족 - 인시던트 대응 프로세스 전면 검토 필요")
        
        if metrics.detection_time_seconds > 300:
            recommendations.append("이상 탐지 시스템의 임계값을 낮추고 알림 채널을 다양화하세요.")
        
        if metrics.impact_score > 50:
            recommendations.append("영향 범위를 제한하기 위한 격리(Circuit Breaker) 메커니즘을 강화하세요.")
        
        # 시나리오별 권고
        if scenario == "model_drift":
            recommendations.extend([
                "A/B 테스트 기반 점진적 배포로 드리프트 영향을 최소화하세요.",
                "자동 롤백 메커니즘을 구현하세요."
            ])
        elif scenario == "data_poisoning":
            recommendations.extend([
                "데이터 출처 검증 및 무결성 체크를 강화하세요.",
                "이상 데이터 격리 프로세스를 자동화하세요."
            ])
        
        recommendations.append("분기별 사고 대응 훈련을 실시하세요.")
        
        return recommendations
    
    def _trigger_callbacks(self, event: str, *args):
        """콜백 트리거"""
        for callback in self._callbacks.get(event, []):
            try:
                callback(*args)
            except Exception as e:
                logger.error(f"콜백 실행 오류 ({event}): {e}")
    
    def get_history(self) -> List[SimulationResult]:
        """시뮬레이션 히스토리 조회"""
        return self._simulation_history
    
    def generate_drill_plan(
        self,
        scenarios: List[str],
        frequency: str = "quarterly"
    ) -> Dict[str, Any]:
        """
        사고 대응 훈련 계획 생성
        
        Args:
            scenarios: 포함할 시나리오 목록
            frequency: 훈련 빈도 (monthly, quarterly, annually)
        
        Returns:
            훈련 계획
        """
        plan = {
            "name": "AI 사고 대응 훈련 계획",
            "frequency": frequency,
            "scenarios": [],
            "participants": ["AI 엔지니어", "MLOps", "보안팀", "경영진"],
            "evaluation_criteria": [
                "SLA 준수 여부",
                "커뮤니케이션 효과성",
                "문서화 품질",
                "복구 절차 숙지도"
            ]
        }
        
        for scenario in scenarios:
            plan["scenarios"].append({
                "name": scenario,
                "severity_levels": ["medium", "high"],
                "duration": "2시간",
                "objectives": [
                    f"{scenario} 탐지 및 에스컬레이션",
                    "영향 범위 파악",
                    "완화 조치 실행",
                    "복구 및 사후 분석"
                ]
            })
        
        return plan
