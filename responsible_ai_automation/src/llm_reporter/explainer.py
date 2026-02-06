"""
메트릭 설명기

복잡한 AI 메트릭을 비전문가도 이해할 수 있도록 설명합니다.
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class MetricExplanation:
    """메트릭 설명 결과"""
    metric_name: str
    value: float
    threshold: float
    status: str  # "pass", "warning", "fail"
    simple_explanation: str
    analogy: str
    recommendation: Optional[str] = None


class MetricExplainer:
    """
    AI 메트릭 설명기
    
    복잡한 기술 메트릭을 일반인도 이해할 수 있는 언어로 설명합니다.
    """
    
    # 메트릭별 기본 설명 템플릿
    METRIC_TEMPLATES = {
        "demographic_parity": {
            "name_ko": "인구통계학적 동등성",
            "description": "서로 다른 집단(예: 성별, 연령)에게 AI가 동등하게 긍정적인 결과를 제공하는지 측정합니다.",
            "analogy": "마치 키 큰 사람과 키 작은 사람 모두에게 같은 확률로 장학금을 주는 것과 같습니다.",
            "good_threshold": 0.8,
            "warning_threshold": 0.6
        },
        "equalized_odds": {
            "name_ko": "균등화된 오즈",
            "description": "AI가 맞추거나 틀릴 때, 모든 집단에서 비슷한 비율로 맞추고 틀리는지 측정합니다.",
            "analogy": "선생님이 채점할 때, 남학생과 여학생 모두에게 같은 기준으로 정답과 오답을 판정하는 것과 같습니다.",
            "good_threshold": 0.85,
            "warning_threshold": 0.7
        },
        "individual_fairness": {
            "name_ko": "개인 공정성",
            "description": "비슷한 특성을 가진 사람들이 비슷한 결과를 받는지 측정합니다.",
            "analogy": "비슷한 실력의 두 지원자가 비슷한 면접 결과를 받는 것과 같습니다.",
            "good_threshold": 0.85,
            "warning_threshold": 0.7
        },
        "transparency_score": {
            "name_ko": "투명성 점수",
            "description": "AI의 결정 이유를 얼마나 잘 설명할 수 있는지 측정합니다.",
            "analogy": "의사가 처방전을 줄 때 왜 그 약을 처방하는지 설명해주는 것과 같습니다.",
            "good_threshold": 0.7,
            "warning_threshold": 0.5
        },
        "robustness_score": {
            "name_ko": "견고성 점수",
            "description": "AI가 약간의 변화나 공격에도 안정적으로 작동하는지 측정합니다.",
            "analogy": "자동차가 울퉁불퉁한 길에서도 안전하게 달릴 수 있는지와 같습니다.",
            "good_threshold": 0.9,
            "warning_threshold": 0.75
        },
        "privacy_score": {
            "name_ko": "프라이버시 점수",
            "description": "AI가 개인정보를 얼마나 잘 보호하는지 측정합니다.",
            "analogy": "은행이 고객의 계좌 정보를 안전하게 보관하는 것과 같습니다.",
            "good_threshold": 0.85,
            "warning_threshold": 0.7
        },
        "accountability_score": {
            "name_ko": "책임성 점수",
            "description": "AI의 결정을 추적하고 문제 발생 시 원인을 찾을 수 있는지 측정합니다.",
            "analogy": "비행기의 블랙박스처럼, 무슨 일이 있었는지 나중에 확인할 수 있는 것과 같습니다.",
            "good_threshold": 0.8,
            "warning_threshold": 0.6
        }
    }
    
    def __init__(self, language: str = "ko"):
        """
        Args:
            language: 출력 언어 (ko, en, ja, zh)
        """
        self.language = language
    
    def explain(
        self,
        metric_name: str,
        value: float,
        threshold: Optional[float] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> MetricExplanation:
        """
        메트릭을 쉬운 언어로 설명
        
        Args:
            metric_name: 메트릭 이름
            value: 측정값
            threshold: 기준값 (없으면 기본값 사용)
            context: 추가 컨텍스트 (산업, 데이터 유형 등)
        
        Returns:
            MetricExplanation 객체
        """
        template = self.METRIC_TEMPLATES.get(metric_name, {})
        
        # 임계값 결정
        good_threshold = threshold or template.get("good_threshold", 0.8)
        warning_threshold = template.get("warning_threshold", 0.6)
        
        # 상태 결정
        if value >= good_threshold:
            status = "pass"
            status_text = "양호"
        elif value >= warning_threshold:
            status = "warning"
            status_text = "주의 필요"
        else:
            status = "fail"
            status_text = "개선 필요"
        
        # 설명 생성
        name_ko = template.get("name_ko", metric_name)
        description = template.get("description", f"{metric_name} 메트릭입니다.")
        analogy = template.get("analogy", "")
        
        simple_explanation = self._generate_simple_explanation(
            name_ko, value, good_threshold, status_text, description
        )
        
        # 권고안 생성
        recommendation = self._generate_recommendation(
            metric_name, value, status, context
        )
        
        return MetricExplanation(
            metric_name=metric_name,
            value=value,
            threshold=good_threshold,
            status=status,
            simple_explanation=simple_explanation,
            analogy=analogy,
            recommendation=recommendation
        )
    
    def _generate_simple_explanation(
        self,
        name: str,
        value: float,
        threshold: float,
        status: str,
        description: str
    ) -> str:
        """간단한 설명 생성"""
        percentage = value * 100
        threshold_pct = threshold * 100
        
        return f"""
**{name}** ({value:.2f})

{description}

현재 점수는 {percentage:.0f}%로, 기준({threshold_pct:.0f}%) 대비 **{status}** 상태입니다.
"""
    
    def _generate_recommendation(
        self,
        metric_name: str,
        value: float,
        status: str,
        context: Optional[Dict[str, Any]]
    ) -> Optional[str]:
        """상태에 따른 권고안 생성"""
        if status == "pass":
            return "현재 상태를 유지하면서 지속적인 모니터링을 권장합니다."
        
        recommendations = {
            "demographic_parity": {
                "warning": "데이터 분포를 확인하고, 언더샘플링된 집단의 데이터를 보강하세요.",
                "fail": "학습 데이터의 집단별 분포를 재검토하고, 공정성 제약조건을 적용한 재학습을 권장합니다."
            },
            "equalized_odds": {
                "warning": "오분류 패턴을 분석하고, 특정 집단에서 오류가 집중되는지 확인하세요.",
                "fail": "집단별 오류율을 균등화하기 위한 후처리 기법 적용을 권장합니다."
            },
            "transparency_score": {
                "warning": "SHAP이나 LIME 같은 설명 도구를 추가로 적용하세요.",
                "fail": "모델 구조를 단순화하거나, 해석 가능한 모델로의 전환을 고려하세요."
            },
            "robustness_score": {
                "warning": "적대적 학습(Adversarial Training)을 부분적으로 적용하세요.",
                "fail": "모델의 견고성 향상을 위한 적대적 학습 및 앙상블 기법을 적용하세요."
            },
            "privacy_score": {
                "warning": "Differential Privacy 파라미터(ε)를 조정하여 프라이버시 보호를 강화하세요.",
                "fail": "민감 데이터 처리 방식을 전면 재검토하고, 강화된 익명화 기법을 적용하세요."
            }
        }
        
        metric_recs = recommendations.get(metric_name, {})
        return metric_recs.get(status, "전문가 검토를 권장합니다.")
    
    def explain_comparison(
        self,
        metric_name: str,
        current_value: float,
        previous_value: float,
        threshold: float
    ) -> str:
        """이전 값과 비교하여 설명"""
        diff = current_value - previous_value
        diff_pct = diff * 100
        
        if diff > 0:
            trend = "향상"
            emoji = "📈"
        elif diff < 0:
            trend = "하락"
            emoji = "📉"
        else:
            trend = "유지"
            emoji = "➡️"
        
        return f"""
{emoji} **{metric_name}** {trend}

- 이전: {previous_value:.2%}
- 현재: {current_value:.2%}
- 변화: {diff_pct:+.1f}%p

{self._get_trend_comment(diff, threshold - current_value)}
"""
    
    def _get_trend_comment(self, diff: float, gap_to_threshold: float) -> str:
        """트렌드에 대한 코멘트 생성"""
        if diff > 0.05:
            return "큰 폭으로 개선되었습니다. 적용된 조치가 효과적입니다."
        elif diff > 0:
            return "소폭 개선되었습니다. 지속적인 모니터링이 필요합니다."
        elif diff < -0.05:
            return "큰 폭으로 하락했습니다. 원인 분석이 필요합니다."
        elif diff < 0:
            return "소폭 하락했습니다. 추가 조치 검토를 권장합니다."
        else:
            return "변화가 없습니다."
    
    def get_all_explanations(
        self,
        metrics: Dict[str, float],
        thresholds: Optional[Dict[str, float]] = None
    ) -> Dict[str, MetricExplanation]:
        """모든 메트릭에 대한 설명 생성"""
        thresholds = thresholds or {}
        explanations = {}
        
        for metric_name, value in metrics.items():
            threshold = thresholds.get(metric_name)
            explanations[metric_name] = self.explain(metric_name, value, threshold)
        
        return explanations
