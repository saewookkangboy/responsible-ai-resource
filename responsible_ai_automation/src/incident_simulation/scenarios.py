"""
사고 시나리오 정의

다양한 AI 사고 시나리오를 정의합니다.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)


class IncidentType(Enum):
    """사고 유형"""
    MODEL_DRIFT = "model_drift"
    DATA_POISONING = "data_poisoning"
    ADVERSARIAL_ATTACK = "adversarial_attack"
    BIAS_AMPLIFICATION = "bias_amplification"
    PRIVACY_BREACH = "privacy_breach"
    SYSTEM_FAILURE = "system_failure"
    PERFORMANCE_DEGRADATION = "performance_degradation"
    HALLUCINATION = "hallucination"  # LLM 환각
    PROMPT_INJECTION = "prompt_injection"


@dataclass
class IncidentScenario(ABC):
    """사고 시나리오 기본 클래스"""
    name: str
    incident_type: IncidentType
    description: str
    severity_levels: List[str]
    indicators: List[str]  # 탐지 지표
    typical_causes: List[str]
    mitigation_steps: List[str]
    
    @abstractmethod
    def inject(self, target_system: Any, severity: str) -> Dict[str, Any]:
        """사고 주입"""
        pass
    
    @abstractmethod
    def verify_detection(self, system_response: Any) -> bool:
        """탐지 검증"""
        pass
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "incident_type": self.incident_type.value,
            "description": self.description,
            "severity_levels": self.severity_levels,
            "indicators": self.indicators,
            "typical_causes": self.typical_causes,
            "mitigation_steps": self.mitigation_steps
        }


@dataclass
class ModelDriftScenario(IncidentScenario):
    """모델 드리프트 시나리오"""
    drift_type: str = "concept"  # concept, data, prior
    drift_magnitude: float = 0.1
    
    def __init__(self):
        super().__init__(
            name="모델 드리프트",
            incident_type=IncidentType.MODEL_DRIFT,
            description="입력 데이터 분포 변화로 인한 모델 성능 저하",
            severity_levels=["low", "medium", "high"],
            indicators=[
                "정확도 급격한 하락",
                "예측 분포 변화",
                "특성 중요도 변화",
                "입력 데이터 통계 변화"
            ],
            typical_causes=[
                "계절적 데이터 패턴 변화",
                "사용자 행동 변화",
                "외부 이벤트 (정책 변경, 경쟁사 등)",
                "데이터 수집 방식 변경"
            ],
            mitigation_steps=[
                "드리프트 원인 분석",
                "모델 재학습 또는 업데이트",
                "특성 엔지니어링 조정",
                "모니터링 임계값 재설정"
            ]
        )
    
    def inject(self, target_system: Any, severity: str) -> Dict[str, Any]:
        """드리프트 주입"""
        magnitude_map = {
            "low": 0.05,
            "medium": 0.15,
            "high": 0.30
        }
        
        self.drift_magnitude = magnitude_map.get(severity, 0.15)
        
        logger.info(f"모델 드리프트 주입: magnitude={self.drift_magnitude}")
        
        return {
            "injected": True,
            "drift_type": self.drift_type,
            "magnitude": self.drift_magnitude,
            "expected_accuracy_drop": self.drift_magnitude * 0.5
        }
    
    def verify_detection(self, system_response: Any) -> bool:
        """드리프트 탐지 검증"""
        if hasattr(system_response, "drift_detected"):
            return system_response.drift_detected
        return False


@dataclass
class DataQualityScenario(IncidentScenario):
    """데이터 품질 저하 시나리오"""
    quality_issue: str = "missing_values"
    affected_features: List[str] = field(default_factory=list)
    
    def __init__(self):
        super().__init__(
            name="데이터 품질 저하",
            incident_type=IncidentType.DATA_POISONING,
            description="입력 데이터의 품질 저하로 인한 모델 오작동",
            severity_levels=["low", "medium", "high", "critical"],
            indicators=[
                "결측값 비율 증가",
                "이상치 빈도 증가",
                "데이터 스키마 불일치",
                "데이터 지연 또는 중복"
            ],
            typical_causes=[
                "데이터 파이프라인 장애",
                "소스 시스템 변경",
                "악의적 데이터 주입",
                "센서/수집기 오작동"
            ],
            mitigation_steps=[
                "데이터 파이프라인 점검",
                "데이터 검증 규칙 강화",
                "폴백 데이터 소스 활성화",
                "영향받은 예측 격리"
            ]
        )
    
    def inject(self, target_system: Any, severity: str) -> Dict[str, Any]:
        """데이터 품질 문제 주입"""
        issue_configs = {
            "low": {"missing_rate": 0.05, "outlier_rate": 0.02},
            "medium": {"missing_rate": 0.15, "outlier_rate": 0.08},
            "high": {"missing_rate": 0.30, "outlier_rate": 0.15},
            "critical": {"missing_rate": 0.50, "outlier_rate": 0.25}
        }
        
        config = issue_configs.get(severity, issue_configs["medium"])
        
        logger.info(f"데이터 품질 문제 주입: {config}")
        
        return {
            "injected": True,
            "quality_issue": self.quality_issue,
            **config
        }
    
    def verify_detection(self, system_response: Any) -> bool:
        """품질 문제 탐지 검증"""
        if hasattr(system_response, "quality_alert"):
            return system_response.quality_alert
        return False


@dataclass
class AdversarialScenario(IncidentScenario):
    """적대적 공격 시나리오"""
    attack_type: str = "evasion"
    perturbation_budget: float = 0.1
    
    def __init__(self):
        super().__init__(
            name="적대적 공격",
            incident_type=IncidentType.ADVERSARIAL_ATTACK,
            description="의도적으로 조작된 입력을 통한 모델 오작동 유도",
            severity_levels=["medium", "high", "critical"],
            indicators=[
                "비정상적 입력 패턴",
                "예측 신뢰도 급격한 변화",
                "모델 출력 이상",
                "요청 패턴 이상"
            ],
            typical_causes=[
                "악의적 사용자",
                "경쟁사 공격",
                "보안 연구자 테스트",
                "자동화된 공격 도구"
            ],
            mitigation_steps=[
                "의심 요청 격리",
                "입력 검증 강화",
                "적대적 학습 적용",
                "요청 속도 제한"
            ]
        )
    
    def inject(self, target_system: Any, severity: str) -> Dict[str, Any]:
        """적대적 공격 주입"""
        attack_configs = {
            "medium": {"perturbation": 0.05, "attack_rate": 0.1},
            "high": {"perturbation": 0.15, "attack_rate": 0.3},
            "critical": {"perturbation": 0.25, "attack_rate": 0.5}
        }
        
        config = attack_configs.get(severity, attack_configs["high"])
        
        logger.info(f"적대적 공격 주입: {config}")
        
        return {
            "injected": True,
            "attack_type": self.attack_type,
            **config
        }
    
    def verify_detection(self, system_response: Any) -> bool:
        """공격 탐지 검증"""
        if hasattr(system_response, "adversarial_detected"):
            return system_response.adversarial_detected
        return False


@dataclass
class LLMHallucinationScenario(IncidentScenario):
    """LLM 환각 시나리오"""
    hallucination_type: str = "factual"  # factual, logical, contextual
    
    def __init__(self):
        super().__init__(
            name="LLM 환각",
            incident_type=IncidentType.HALLUCINATION,
            description="LLM이 사실이 아닌 정보를 자신있게 생성",
            severity_levels=["low", "medium", "high", "critical"],
            indicators=[
                "사실 확인 실패율 증가",
                "사용자 피드백 부정적",
                "출력 일관성 저하",
                "외부 지식과 불일치"
            ],
            typical_causes=[
                "학습 데이터 품질 문제",
                "프롬프트 설계 문제",
                "컨텍스트 부족",
                "모델 과신"
            ],
            mitigation_steps=[
                "RAG(Retrieval-Augmented Generation) 적용",
                "출력 검증 파이프라인 추가",
                "신뢰도 임계값 설정",
                "인간 검토 프로세스"
            ]
        )
    
    def inject(self, target_system: Any, severity: str) -> Dict[str, Any]:
        """환각 유도 조건 주입"""
        configs = {
            "low": {"context_removal": 0.1, "temperature_boost": 0.1},
            "medium": {"context_removal": 0.3, "temperature_boost": 0.3},
            "high": {"context_removal": 0.5, "temperature_boost": 0.5},
            "critical": {"context_removal": 0.8, "temperature_boost": 0.7}
        }
        
        config = configs.get(severity, configs["medium"])
        
        logger.info(f"환각 유도 조건 주입: {config}")
        
        return {
            "injected": True,
            "hallucination_type": self.hallucination_type,
            **config
        }
    
    def verify_detection(self, system_response: Any) -> bool:
        """환각 탐지 검증"""
        if hasattr(system_response, "hallucination_score"):
            return system_response.hallucination_score > 0.5
        return False


class ScenarioLibrary:
    """시나리오 라이브러리"""
    
    _scenarios: Dict[IncidentType, IncidentScenario] = {}
    
    @classmethod
    def register(cls, scenario: IncidentScenario):
        """시나리오 등록"""
        cls._scenarios[scenario.incident_type] = scenario
    
    @classmethod
    def get(cls, incident_type: IncidentType) -> Optional[IncidentScenario]:
        """시나리오 조회"""
        return cls._scenarios.get(incident_type)
    
    @classmethod
    def list_all(cls) -> List[IncidentScenario]:
        """모든 시나리오 목록"""
        return list(cls._scenarios.values())
    
    @classmethod
    def load_defaults(cls):
        """기본 시나리오 로드"""
        cls.register(ModelDriftScenario())
        cls.register(DataQualityScenario())
        cls.register(AdversarialScenario())
        cls.register(LLMHallucinationScenario())


# 기본 시나리오 로드
ScenarioLibrary.load_defaults()
