"""
정책 검증기

AI 시스템이 정의된 거버넌스 정책을 준수하는지 검증합니다.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import logging

from .policy import (
    GovernancePolicy, 
    PolicySpec,
    EnforcementLevel,
    MetricRequirement
)

logger = logging.getLogger(__name__)


class ViolationSeverity(Enum):
    """위반 심각도"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class PolicyViolation:
    """정책 위반"""
    policy_area: str  # fairness, transparency, privacy, etc.
    requirement: str
    expected: Any
    actual: Any
    severity: ViolationSeverity
    message: str
    recommendation: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "policy_area": self.policy_area,
            "requirement": self.requirement,
            "expected": str(self.expected),
            "actual": str(self.actual),
            "severity": self.severity.value,
            "message": self.message,
            "recommendation": self.recommendation
        }


@dataclass
class ValidationResult:
    """검증 결과"""
    passed: bool
    policy_name: str
    policy_version: str
    timestamp: datetime
    violations: List[PolicyViolation] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metrics: Dict[str, float] = field(default_factory=dict)
    enforcement_action: Optional[EnforcementLevel] = None
    
    @property
    def violation_count(self) -> int:
        return len(self.violations)
    
    @property
    def critical_count(self) -> int:
        return sum(1 for v in self.violations if v.severity == ViolationSeverity.CRITICAL)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "passed": self.passed,
            "policy_name": self.policy_name,
            "policy_version": self.policy_version,
            "timestamp": self.timestamp.isoformat(),
            "violation_count": self.violation_count,
            "critical_count": self.critical_count,
            "violations": [v.to_dict() for v in self.violations],
            "warnings": self.warnings,
            "metrics": self.metrics,
            "enforcement_action": self.enforcement_action.value if self.enforcement_action else None
        }
    
    def to_markdown(self) -> str:
        """마크다운 리포트 생성"""
        status = "✅ PASSED" if self.passed else "❌ FAILED"
        
        md = f"""# 정책 검증 결과

**상태**: {status}  
**정책**: {self.policy_name} v{self.policy_version}  
**검증 일시**: {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}

## 요약

- 총 위반: {self.violation_count}건
- Critical: {self.critical_count}건
- 조치: {self.enforcement_action.value if self.enforcement_action else 'N/A'}

"""
        if self.violations:
            md += "## 위반 사항\n\n"
            for v in self.violations:
                md += f"""### [{v.severity.value.upper()}] {v.policy_area}

- **요구사항**: {v.requirement}
- **기대값**: {v.expected}
- **실제값**: {v.actual}
- **메시지**: {v.message}
- **권고사항**: {v.recommendation}

"""
        
        if self.warnings:
            md += "## 경고\n\n"
            for w in self.warnings:
                md += f"- {w}\n"
        
        if self.metrics:
            md += "\n## 측정된 메트릭\n\n"
            md += "| 메트릭 | 값 |\n|--------|----|\n"
            for name, value in self.metrics.items():
                md += f"| {name} | {value:.4f} |\n"
        
        return md


class PolicyValidator:
    """
    정책 검증기
    
    AI 시스템이 거버넌스 정책을 준수하는지 검증합니다.
    
    Example:
        >>> policy = GovernancePolicy.from_yaml("policy.yaml")
        >>> validator = PolicyValidator(policy)
        >>> result = validator.validate(model, data)
        >>> if not result.passed:
        ...     print("위반:", result.violations)
    """
    
    def __init__(self, policy: GovernancePolicy):
        """
        Args:
            policy: 검증에 사용할 거버넌스 정책
        """
        self.policy = policy
        self._evaluators = {}
        self._register_default_evaluators()
    
    def _register_default_evaluators(self):
        """기본 평가기 등록"""
        self._evaluators = {
            "fairness": self._validate_fairness,
            "transparency": self._validate_transparency,
            "privacy": self._validate_privacy,
            "robustness": self._validate_robustness,
            "sustainability": self._validate_sustainability,
        }
    
    def validate(
        self,
        model: Any = None,
        data: Any = None,
        metrics: Optional[Dict[str, float]] = None
    ) -> ValidationResult:
        """
        정책 검증 실행
        
        Args:
            model: 검증 대상 모델
            data: 검증에 사용할 데이터
            metrics: 사전 계산된 메트릭 (선택)
        
        Returns:
            ValidationResult: 검증 결과
        """
        violations = []
        warnings = []
        all_metrics = metrics or {}
        
        logger.info(f"정책 검증 시작: {self.policy.metadata.name}")
        
        # 정책 유효성 확인
        if not self.policy.is_effective():
            warnings.append(f"정책이 아직 발효되지 않음 (발효일: {self.policy.metadata.effective_date})")
        
        # 각 영역별 검증
        spec = self.policy.spec
        
        if spec.fairness.enabled:
            fairness_violations, fairness_metrics = self._validate_fairness(model, data, metrics)
            violations.extend(fairness_violations)
            all_metrics.update(fairness_metrics)
        
        if spec.transparency.enabled:
            trans_violations, trans_metrics = self._validate_transparency(model, metrics)
            violations.extend(trans_violations)
            all_metrics.update(trans_metrics)
        
        if spec.privacy.enabled:
            privacy_violations, privacy_metrics = self._validate_privacy(model, data, metrics)
            violations.extend(privacy_violations)
            all_metrics.update(privacy_metrics)
        
        if spec.robustness.enabled:
            robust_violations, robust_metrics = self._validate_robustness(model, metrics)
            violations.extend(robust_violations)
            all_metrics.update(robust_metrics)
        
        if spec.sustainability.enabled:
            sustain_violations, sustain_metrics = self._validate_sustainability(metrics)
            violations.extend(sustain_violations)
            all_metrics.update(sustain_metrics)
        
        # 조치 결정
        enforcement_action = self._determine_enforcement(violations)
        
        # 결과 생성
        passed = len(violations) == 0 or enforcement_action in [
            EnforcementLevel.WARN, 
            EnforcementLevel.LOG
        ]
        
        result = ValidationResult(
            passed=passed,
            policy_name=self.policy.metadata.name,
            policy_version=self.policy.metadata.version,
            timestamp=datetime.now(),
            violations=violations,
            warnings=warnings,
            metrics=all_metrics,
            enforcement_action=enforcement_action
        )
        
        logger.info(f"정책 검증 완료: passed={passed}, violations={len(violations)}")
        return result
    
    def _validate_fairness(
        self,
        model: Any,
        data: Any,
        metrics: Optional[Dict[str, float]]
    ) -> tuple:
        """공정성 검증"""
        violations = []
        measured_metrics = {}
        
        fairness_policy = self.policy.spec.fairness
        
        # 메트릭 요구사항 검증
        for req in fairness_policy.metrics:
            metric_value = None
            
            if metrics and req.name in metrics:
                metric_value = metrics[req.name]
            else:
                # 실제 평가 수행
                metric_value = self._evaluate_fairness_metric(model, data, req.name)
            
            if metric_value is not None:
                measured_metrics[f"fairness_{req.name}"] = metric_value
                
                if not req.is_satisfied(metric_value):
                    violations.append(PolicyViolation(
                        policy_area="fairness",
                        requirement=req.name,
                        expected=f"{req.operator} {req.threshold}",
                        actual=metric_value,
                        severity=self._requirement_to_severity(req),
                        message=f"{req.name} 메트릭이 요구사항을 충족하지 않습니다.",
                        recommendation="학습 데이터의 균형을 확인하고 공정성 제약조건을 적용하세요."
                    ))
        
        return violations, measured_metrics
    
    def _validate_transparency(
        self,
        model: Any,
        metrics: Optional[Dict[str, float]]
    ) -> tuple:
        """투명성 검증"""
        violations = []
        measured_metrics = {}
        
        trans_policy = self.policy.spec.transparency
        
        # 설명 가능성 점수
        explainability = metrics.get("explainability_score") if metrics else None
        if explainability is None:
            explainability = self._evaluate_explainability(model)
        
        if explainability is not None:
            measured_metrics["transparency_explainability"] = explainability
            
            if explainability < trans_policy.explainability_score:
                violations.append(PolicyViolation(
                    policy_area="transparency",
                    requirement="explainability_score",
                    expected=f">= {trans_policy.explainability_score}",
                    actual=explainability,
                    severity=ViolationSeverity.MEDIUM,
                    message="설명 가능성 점수가 요구사항에 미달합니다.",
                    recommendation="SHAP, LIME 등 설명 도구를 적용하거나 해석 가능한 모델을 고려하세요."
                ))
        
        # 모델 카드 확인
        if trans_policy.model_card_required:
            has_model_card = self._check_model_card(model)
            if not has_model_card:
                violations.append(PolicyViolation(
                    policy_area="transparency",
                    requirement="model_card_required",
                    expected=True,
                    actual=False,
                    severity=ViolationSeverity.LOW,
                    message="모델 카드가 문서화되지 않았습니다.",
                    recommendation="모델 카드를 작성하여 모델의 특성, 한계, 사용 목적을 문서화하세요."
                ))
        
        return violations, measured_metrics
    
    def _validate_privacy(
        self,
        model: Any,
        data: Any,
        metrics: Optional[Dict[str, float]]
    ) -> tuple:
        """프라이버시 검증"""
        violations = []
        measured_metrics = {}
        
        privacy_policy = self.policy.spec.privacy
        
        # Differential Privacy epsilon
        dp_epsilon = metrics.get("dp_epsilon") if metrics else None
        
        if dp_epsilon is not None:
            measured_metrics["privacy_dp_epsilon"] = dp_epsilon
            
            if dp_epsilon > privacy_policy.differential_privacy_epsilon:
                violations.append(PolicyViolation(
                    policy_area="privacy",
                    requirement="differential_privacy_epsilon",
                    expected=f"<= {privacy_policy.differential_privacy_epsilon}",
                    actual=dp_epsilon,
                    severity=ViolationSeverity.HIGH,
                    message="Differential Privacy epsilon이 기준을 초과합니다.",
                    recommendation="프라이버시 버짓을 줄이거나 노이즈를 추가하세요."
                ))
        
        # PII 감지
        if privacy_policy.pii_detection:
            pii_detected = self._detect_pii(data)
            if pii_detected:
                violations.append(PolicyViolation(
                    policy_area="privacy",
                    requirement="pii_detection",
                    expected="No PII",
                    actual="PII detected",
                    severity=ViolationSeverity.CRITICAL,
                    message="데이터에서 개인식별정보(PII)가 감지되었습니다.",
                    recommendation="데이터 익명화 또는 마스킹을 적용하세요."
                ))
        
        return violations, measured_metrics
    
    def _validate_robustness(
        self,
        model: Any,
        metrics: Optional[Dict[str, float]]
    ) -> tuple:
        """견고성 검증"""
        violations = []
        measured_metrics = {}
        
        robust_policy = self.policy.spec.robustness
        
        # 적대적 견고성
        adv_robustness = metrics.get("adversarial_robustness") if metrics else None
        
        if adv_robustness is not None:
            measured_metrics["robustness_adversarial"] = adv_robustness
            
            if adv_robustness < robust_policy.adversarial_robustness:
                violations.append(PolicyViolation(
                    policy_area="robustness",
                    requirement="adversarial_robustness",
                    expected=f">= {robust_policy.adversarial_robustness}",
                    actual=adv_robustness,
                    severity=ViolationSeverity.MEDIUM,
                    message="적대적 공격에 대한 견고성이 부족합니다.",
                    recommendation="적대적 학습(Adversarial Training)을 적용하세요."
                ))
        
        return violations, measured_metrics
    
    def _validate_sustainability(
        self,
        metrics: Optional[Dict[str, float]]
    ) -> tuple:
        """지속가능성 검증"""
        violations = []
        measured_metrics = {}
        
        sustain_policy = self.policy.spec.sustainability
        
        # 탄소 발자국
        carbon = metrics.get("carbon_footprint_kg") if metrics else None
        
        if carbon is not None:
            measured_metrics["sustainability_carbon"] = carbon
            
            if carbon > sustain_policy.max_carbon_footprint_kg:
                violations.append(PolicyViolation(
                    policy_area="sustainability",
                    requirement="max_carbon_footprint_kg",
                    expected=f"<= {sustain_policy.max_carbon_footprint_kg}",
                    actual=carbon,
                    severity=ViolationSeverity.LOW,
                    message="탄소 발자국이 기준을 초과합니다.",
                    recommendation="모델 경량화 또는 효율적인 학습 방법을 적용하세요."
                ))
        
        return violations, measured_metrics
    
    def _determine_enforcement(
        self,
        violations: List[PolicyViolation]
    ) -> EnforcementLevel:
        """위반에 따른 조치 결정"""
        enforcement = self.policy.spec.enforcement
        
        if any(v.severity == ViolationSeverity.CRITICAL for v in violations):
            return enforcement.critical
        elif any(v.severity == ViolationSeverity.HIGH for v in violations):
            return enforcement.high
        elif any(v.severity == ViolationSeverity.MEDIUM for v in violations):
            return enforcement.medium
        elif any(v.severity == ViolationSeverity.LOW for v in violations):
            return enforcement.low
        else:
            return EnforcementLevel.LOG
    
    def _requirement_to_severity(self, req: MetricRequirement) -> ViolationSeverity:
        """요구사항의 action을 severity로 변환"""
        mapping = {
            EnforcementLevel.BLOCK: ViolationSeverity.CRITICAL,
            EnforcementLevel.REQUIRE_APPROVAL: ViolationSeverity.HIGH,
            EnforcementLevel.WARN: ViolationSeverity.MEDIUM,
            EnforcementLevel.LOG: ViolationSeverity.LOW,
        }
        return mapping.get(req.action, ViolationSeverity.MEDIUM)
    
    # 평가 헬퍼 메서드들 (실제 구현은 evaluation 모듈과 연동)
    def _evaluate_fairness_metric(self, model, data, metric_name) -> Optional[float]:
        """공정성 메트릭 평가 (stub)"""
        # 실제 구현에서는 evaluation 모듈 사용
        return None
    
    def _evaluate_explainability(self, model) -> Optional[float]:
        """설명 가능성 평가 (stub)"""
        return None
    
    def _check_model_card(self, model) -> bool:
        """모델 카드 존재 여부 확인"""
        return hasattr(model, 'model_card') or hasattr(model, '__doc__')
    
    def _detect_pii(self, data) -> bool:
        """PII 감지 (stub)"""
        return False
