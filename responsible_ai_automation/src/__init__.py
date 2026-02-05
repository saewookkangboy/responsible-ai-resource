"""
Responsible AI Automation - 차별화 기능 모듈

이 패키지는 기존 Responsible AI 도구들과 차별화되는 고급 기능을 제공합니다.

모듈 구성:
-----------
1. llm_reporter: LLM 기반 자동 설명 리포트 생성
2. red_team: AI Red Team 자동화
3. governance: AI Governance as Code (GaC)
4. agent_monitor: AI Agent 행동 모니터링
5. carbon_tracker: AI 탄소 발자국 추적
6. regulation: 글로벌 규제 자동 매핑
7. multimodal: 멀티모달 AI 공정성 검증
8. incident_simulation: AI 사고 시뮬레이션

사용 예시:
----------
>>> # LLM 기반 리포트 생성
>>> from src.llm_reporter import LLMReportGenerator
>>> generator = LLMReportGenerator()
>>> report = generator.generate_report(results, audience="executive")

>>> # AI Red Team 테스트
>>> from src.red_team import AIRedTeam
>>> red_team = AIRedTeam()
>>> vulnerabilities = red_team.run_comprehensive_test(model)

>>> # 탄소 발자국 추적
>>> from src.carbon_tracker import CarbonFootprintTracker
>>> with CarbonFootprintTracker().track("training"):
...     model.train()

>>> # 멀티모달 공정성 검증
>>> from src.multimodal import MultimodalFairnessValidator
>>> validator = MultimodalFairnessValidator()
>>> results = validator.validate(model, test_data, ModalityType.IMAGE)

버전 정보:
----------
"""

# 버전 정보
__version__ = "0.2.0"
__author__ = "Responsible AI Team"

# 차별화 기능 모듈 임포트
try:
    from .llm_reporter import LLMReportGenerator, ReportTemplate
except ImportError:
    LLMReportGenerator = None
    ReportTemplate = None

try:
    from .red_team import AIRedTeam, AttackVector
except ImportError:
    AIRedTeam = None
    AttackVector = None

try:
    from .governance import GovernancePolicy, PolicyValidator
except ImportError:
    GovernancePolicy = None
    PolicyValidator = None

try:
    from .agent_monitor import AIAgentMonitor, CircuitBreaker
except ImportError:
    AIAgentMonitor = None
    CircuitBreaker = None

try:
    from .carbon_tracker import CarbonFootprintTracker, CarbonCalculator
except ImportError:
    CarbonFootprintTracker = None
    CarbonCalculator = None

try:
    from .regulation import GlobalRegulationMapper, ComplianceAnalyzer
except ImportError:
    GlobalRegulationMapper = None
    ComplianceAnalyzer = None

try:
    from .multimodal import MultimodalFairnessValidator, FacialRecognitionBiasTester
except ImportError:
    MultimodalFairnessValidator = None
    FacialRecognitionBiasTester = None

try:
    from .incident_simulation import AIIncidentSimulator, IncidentType
except ImportError:
    AIIncidentSimulator = None
    IncidentType = None


__all__ = [
    # LLM Reporter
    "LLMReportGenerator",
    "ReportTemplate",
    
    # Red Team
    "AIRedTeam",
    "AttackVector",
    
    # Governance
    "GovernancePolicy",
    "PolicyValidator",
    
    # Agent Monitor
    "AIAgentMonitor",
    "CircuitBreaker",
    
    # Carbon Tracker
    "CarbonFootprintTracker",
    "CarbonCalculator",
    
    # Regulation
    "GlobalRegulationMapper",
    "ComplianceAnalyzer",
    
    # Multimodal
    "MultimodalFairnessValidator",
    "FacialRecognitionBiasTester",
    
    # Incident Simulation
    "AIIncidentSimulator",
    "IncidentType",
]


def get_available_modules() -> dict:
    """
    사용 가능한 모듈 목록 반환
    
    Returns:
        모듈명과 가용 여부를 담은 딕셔너리
    """
    return {
        "llm_reporter": LLMReportGenerator is not None,
        "red_team": AIRedTeam is not None,
        "governance": GovernancePolicy is not None,
        "agent_monitor": AIAgentMonitor is not None,
        "carbon_tracker": CarbonFootprintTracker is not None,
        "regulation": GlobalRegulationMapper is not None,
        "multimodal": MultimodalFairnessValidator is not None,
        "incident_simulation": AIIncidentSimulator is not None,
    }


def print_status():
    """모듈 상태 출력"""
    modules = get_available_modules()
    print("\n🤖 Responsible AI Automation - 차별화 기능 모듈 상태\n")
    print(f"버전: {__version__}")
    print("-" * 50)
    
    for module, available in modules.items():
        status = "✅" if available else "❌"
        print(f"{status} {module}")
    
    print("-" * 50)
    available_count = sum(modules.values())
    print(f"총 {len(modules)}개 중 {available_count}개 모듈 사용 가능\n")
