"""
AI 사고 시뮬레이션 모듈

AI 장애/사고 시나리오를 시뮬레이션하여 대응 역량을 테스트합니다.

주요 기능:
- 모델 드리프트 시뮬레이션
- 데이터 품질 저하 시나리오
- 적대적 공격 시뮬레이션
- 시스템 장애 복구 테스트
- 대응 훈련 및 리포트

사용 예시:
    from src.incident_simulation import AIIncidentSimulator, IncidentType
    
    simulator = AIIncidentSimulator()
    
    # 모델 드리프트 시뮬레이션
    result = simulator.simulate(
        scenario=IncidentType.MODEL_DRIFT,
        target_system=my_ai_system,
        severity="high"
    )
    
    # 대응 결과 평가
    print(f"탐지 시간: {result.detection_time_seconds}초")
    print(f"복구 시간: {result.recovery_time_seconds}초")
"""

from .simulator import AIIncidentSimulator, SimulationResult
from .scenarios import (
    IncidentType,
    IncidentScenario,
    ModelDriftScenario,
    DataQualityScenario,
    AdversarialScenario
)
from .response import ResponseEvaluator, ResponseReport

__all__ = [
    "AIIncidentSimulator",
    "SimulationResult",
    "IncidentType",
    "IncidentScenario",
    "ModelDriftScenario",
    "DataQualityScenario",
    "AdversarialScenario",
    "ResponseEvaluator",
    "ResponseReport",
]

__version__ = "0.1.0"
