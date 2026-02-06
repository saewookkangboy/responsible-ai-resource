"""
AI Red Team 자동화 모듈

AI 시스템의 윤리적 취약점을 자동으로 발견하고 테스트합니다.

주요 기능:
- Prompt Injection 테스트
- Jailbreak 시뮬레이션
- 적대적 공격 시나리오 자동 생성
- 취약점 리포트 생성

사용 예시:
    from src.red_team import AIRedTeam, AttackVector
    
    red_team = AIRedTeam()
    report = red_team.run_comprehensive_test(
        target_model=model,
        attack_vectors=[AttackVector.PROMPT_INJECTION, AttackVector.JAILBREAK]
    )
"""

from .red_team import AIRedTeam, RedTeamReport
from .attacks import (
    AttackVector,
    PromptInjectionTester,
    JailbreakTester,
    AdversarialTester,
    BiasExploitTester
)
from .payloads import PayloadLibrary, CustomPayload

__all__ = [
    "AIRedTeam",
    "RedTeamReport",
    "AttackVector",
    "PromptInjectionTester",
    "JailbreakTester",
    "AdversarialTester",
    "BiasExploitTester",
    "PayloadLibrary",
    "CustomPayload",
]

__version__ = "0.1.0"
