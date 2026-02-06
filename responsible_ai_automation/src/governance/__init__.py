"""
AI Governance as Code (GaC) 모듈

AI 거버넌스 정책을 코드로 정의하고, 자동으로 검증/적용하는 GitOps 스타일 거버넌스 시스템입니다.

주요 기능:
- YAML/JSON 기반 정책 정의
- CI/CD 파이프라인 통합
- 정책 버전 관리
- 자동 검증 및 리포트

사용 예시:
    from src.governance import GovernancePolicy, PolicyValidator
    
    # 정책 로드
    policy = GovernancePolicy.from_yaml("ai-governance-policy.yaml")
    
    # 검증 실행
    validator = PolicyValidator(policy)
    result = validator.validate(model, data)
    
    if not result.passed:
        print("정책 위반:", result.violations)
"""

from .policy import GovernancePolicy, PolicySpec
from .validator import PolicyValidator, ValidationResult
from .enforcement import PolicyEnforcer, EnforcementAction
from .templates import PolicyTemplate, TemplateLibrary

__all__ = [
    "GovernancePolicy",
    "PolicySpec",
    "PolicyValidator",
    "ValidationResult",
    "PolicyEnforcer",
    "EnforcementAction",
    "PolicyTemplate",
    "TemplateLibrary",
]

__version__ = "0.1.0"
