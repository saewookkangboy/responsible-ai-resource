"""
얼굴 인식 편향 테스터

얼굴 인식/검출 모델의 인구통계적 편향을 테스트합니다.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class DemographicGroup(Enum):
    """인구통계 그룹"""
    # 피부톤 (Fitzpatrick 스케일 기반)
    SKIN_TYPE_1 = "skin_type_1"  # 매우 밝음
    SKIN_TYPE_2 = "skin_type_2"  # 밝음
    SKIN_TYPE_3 = "skin_type_3"  # 중간 밝음
    SKIN_TYPE_4 = "skin_type_4"  # 중간 어두움
    SKIN_TYPE_5 = "skin_type_5"  # 어두움
    SKIN_TYPE_6 = "skin_type_6"  # 매우 어두움
    
    # 성별
    MALE = "male"
    FEMALE = "female"
    
    # 연령대
    CHILD = "child"           # 0-12
    TEENAGER = "teenager"     # 13-19
    YOUNG_ADULT = "young_adult"  # 20-35
    MIDDLE_AGED = "middle_aged"  # 36-55
    SENIOR = "senior"         # 56+


@dataclass
class FacialBiasMetrics:
    """얼굴 인식 편향 지표"""
    group: DemographicGroup
    detection_rate: float       # 얼굴 검출률
    recognition_accuracy: float # 인식 정확도
    false_match_rate: float     # 오일치율 (FAR)
    false_non_match_rate: float # 미일치율 (FRR)
    verification_accuracy: float # 검증 정확도
    sample_count: int
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "group": self.group.value,
            "detection_rate": self.detection_rate,
            "recognition_accuracy": self.recognition_accuracy,
            "false_match_rate": self.false_match_rate,
            "false_non_match_rate": self.false_non_match_rate,
            "verification_accuracy": self.verification_accuracy,
            "sample_count": self.sample_count
        }


@dataclass
class FacialBiasReport:
    """얼굴 인식 편향 리포트"""
    model_name: str
    total_samples: int
    metrics_by_group: Dict[str, FacialBiasMetrics]
    intersectional_analysis: Dict[str, FacialBiasMetrics]  # 교차 분석 (예: 성별+피부톤)
    worst_detection_group: str
    worst_recognition_group: str
    overall_bias_score: float  # 0-100 (높을수록 편향 심함)
    recommendations: List[str]
    
    def to_markdown(self) -> str:
        """마크다운 리포트"""
        md = f"""# 얼굴 인식 편향 분석 리포트

**모델**: {self.model_name}  
**총 샘플**: {self.total_samples}  
**편향 점수**: {self.overall_bias_score:.1f}/100 (낮을수록 양호)

## 그룹별 성능

| 그룹 | 검출률 | 인식 정확도 | FAR | FRR |
|------|--------|-------------|-----|-----|
"""
        for name, metrics in self.metrics_by_group.items():
            md += f"| {name} | {metrics.detection_rate:.2%} | {metrics.recognition_accuracy:.2%} | {metrics.false_match_rate:.4f} | {metrics.false_non_match_rate:.4f} |\n"
        
        md += f"""
## 주요 발견

- **검출률 최저 그룹**: {self.worst_detection_group}
- **인식 정확도 최저 그룹**: {self.worst_recognition_group}

## 권고사항

"""
        for i, rec in enumerate(self.recommendations, 1):
            md += f"{i}. {rec}\n"
        
        return md


class FacialRecognitionBiasTester:
    """
    얼굴 인식 편향 테스터
    
    얼굴 인식/검출 모델의 다양한 인구통계 그룹에 대한 성능 편향을 테스트합니다.
    
    Example:
        >>> tester = FacialRecognitionBiasTester()
        >>> report = tester.test(
        ...     model=face_model,
        ...     test_images=diverse_face_images,
        ...     demographic_labels=labels
        ... )
    """
    
    # NIST FRVT 기준 임계값
    NIST_THRESHOLDS = {
        "false_match_rate": 0.0001,    # 1:10,000
        "detection_rate_min": 0.95,     # 95% 이상
        "accuracy_disparity": 0.03,     # 3% 이하 격차
    }
    
    def __init__(
        self,
        thresholds: Optional[Dict[str, float]] = None
    ):
        self.thresholds = thresholds or self.NIST_THRESHOLDS.copy()
        logger.info("FacialRecognitionBiasTester 초기화")
    
    def test(
        self,
        model: Any,
        test_images: List[Any],
        demographic_labels: Dict[str, DemographicGroup],
        model_name: str = "Unknown"
    ) -> FacialBiasReport:
        """
        얼굴 인식 편향 테스트 수행
        
        Args:
            model: 테스트 대상 모델
            test_images: 테스트 이미지 목록
            demographic_labels: 이미지별 인구통계 레이블
            model_name: 모델 이름
        
        Returns:
            FacialBiasReport 객체
        """
        # 그룹별 테스트 수행
        metrics_by_group = self._test_by_group(model, test_images, demographic_labels)
        
        # 교차 분석
        intersectional = self._intersectional_analysis(
            model, test_images, demographic_labels
        )
        
        # 최악 성능 그룹 식별
        worst_detection = min(
            metrics_by_group.items(),
            key=lambda x: x[1].detection_rate
        )[0]
        worst_recognition = min(
            metrics_by_group.items(),
            key=lambda x: x[1].recognition_accuracy
        )[0]
        
        # 편향 점수 계산
        bias_score = self._calculate_bias_score(metrics_by_group)
        
        # 권고사항 생성
        recommendations = self._generate_recommendations(
            metrics_by_group, worst_detection, worst_recognition
        )
        
        return FacialBiasReport(
            model_name=model_name,
            total_samples=len(test_images),
            metrics_by_group=metrics_by_group,
            intersectional_analysis=intersectional,
            worst_detection_group=worst_detection,
            worst_recognition_group=worst_recognition,
            overall_bias_score=bias_score,
            recommendations=recommendations
        )
    
    def _test_by_group(
        self,
        model: Any,
        test_images: List[Any],
        demographic_labels: Dict[str, DemographicGroup]
    ) -> Dict[str, FacialBiasMetrics]:
        """그룹별 테스트"""
        # 시뮬레이션 데이터
        # 실제 구현에서는 모델 예측 수행
        
        return {
            "skin_type_1_2": FacialBiasMetrics(
                group=DemographicGroup.SKIN_TYPE_1,
                detection_rate=0.98,
                recognition_accuracy=0.95,
                false_match_rate=0.0001,
                false_non_match_rate=0.01,
                verification_accuracy=0.96,
                sample_count=1000
            ),
            "skin_type_3_4": FacialBiasMetrics(
                group=DemographicGroup.SKIN_TYPE_3,
                detection_rate=0.96,
                recognition_accuracy=0.92,
                false_match_rate=0.0002,
                false_non_match_rate=0.02,
                verification_accuracy=0.93,
                sample_count=1000
            ),
            "skin_type_5_6": FacialBiasMetrics(
                group=DemographicGroup.SKIN_TYPE_5,
                detection_rate=0.91,
                recognition_accuracy=0.85,
                false_match_rate=0.0005,
                false_non_match_rate=0.04,
                verification_accuracy=0.87,
                sample_count=1000
            ),
            "male": FacialBiasMetrics(
                group=DemographicGroup.MALE,
                detection_rate=0.97,
                recognition_accuracy=0.93,
                false_match_rate=0.0002,
                false_non_match_rate=0.015,
                verification_accuracy=0.94,
                sample_count=1500
            ),
            "female": FacialBiasMetrics(
                group=DemographicGroup.FEMALE,
                detection_rate=0.95,
                recognition_accuracy=0.90,
                false_match_rate=0.0003,
                false_non_match_rate=0.025,
                verification_accuracy=0.91,
                sample_count=1500
            ),
        }
    
    def _intersectional_analysis(
        self,
        model: Any,
        test_images: List[Any],
        demographic_labels: Dict[str, DemographicGroup]
    ) -> Dict[str, FacialBiasMetrics]:
        """교차 분석 (예: 성별 x 피부톤)"""
        # 시뮬레이션 데이터
        return {
            "dark_female": FacialBiasMetrics(
                group=DemographicGroup.SKIN_TYPE_5,
                detection_rate=0.88,
                recognition_accuracy=0.82,
                false_match_rate=0.0006,
                false_non_match_rate=0.05,
                verification_accuracy=0.84,
                sample_count=500
            ),
            "light_male": FacialBiasMetrics(
                group=DemographicGroup.SKIN_TYPE_1,
                detection_rate=0.99,
                recognition_accuracy=0.97,
                false_match_rate=0.00008,
                false_non_match_rate=0.008,
                verification_accuracy=0.97,
                sample_count=500
            ),
        }
    
    def _calculate_bias_score(
        self,
        metrics_by_group: Dict[str, FacialBiasMetrics]
    ) -> float:
        """편향 점수 계산 (0-100, 낮을수록 양호)"""
        if not metrics_by_group:
            return 0.0
        
        metrics_list = list(metrics_by_group.values())
        
        # 검출률 격차
        detection_rates = [m.detection_rate for m in metrics_list]
        detection_disparity = max(detection_rates) - min(detection_rates)
        
        # 인식 정확도 격차
        accuracies = [m.recognition_accuracy for m in metrics_list]
        accuracy_disparity = max(accuracies) - min(accuracies)
        
        # FAR 격차
        fars = [m.false_match_rate for m in metrics_list]
        far_disparity = max(fars) - min(fars) if max(fars) > 0 else 0
        far_ratio = max(fars) / max(min(fars), 0.00001)
        
        # 편향 점수 (가중 평균)
        score = (
            detection_disparity * 30 +    # 검출률 30%
            accuracy_disparity * 40 +      # 정확도 40%
            min(far_ratio / 10, 1) * 30    # FAR 비율 30%
        ) * 100
        
        return min(score, 100)
    
    def _generate_recommendations(
        self,
        metrics_by_group: Dict[str, FacialBiasMetrics],
        worst_detection: str,
        worst_recognition: str
    ) -> List[str]:
        """권고사항 생성"""
        recommendations = []
        
        # 검출률 저성능 그룹
        recommendations.append(
            f"'{worst_detection}' 그룹의 검출률 개선을 위해 "
            f"해당 그룹의 학습 이미지를 증강하세요."
        )
        
        # 인식 정확도 저성능 그룹
        if worst_recognition != worst_detection:
            recommendations.append(
                f"'{worst_recognition}' 그룹의 인식 정확도 개선이 필요합니다."
            )
        
        # 일반 권고
        recommendations.extend([
            "다양한 조명 조건(역광, 측광, 저조도)의 이미지를 포함하세요.",
            "다양한 포즈와 표정의 이미지로 학습 데이터를 보강하세요.",
            "고해상도와 저해상도 이미지 모두에서 성능을 테스트하세요.",
            "NIST FRVT 기준에 따른 정기적인 편향 평가를 수행하세요."
        ])
        
        return recommendations
    
    def test_against_nist_standards(
        self,
        model: Any,
        test_images: List[Any],
        demographic_labels: Dict[str, DemographicGroup]
    ) -> Dict[str, bool]:
        """NIST FRVT 기준 대비 테스트"""
        report = self.test(model, test_images, demographic_labels)
        
        results = {}
        
        # 모든 그룹 검출률 95% 이상
        all_detection_pass = all(
            m.detection_rate >= self.thresholds["detection_rate_min"]
            for m in report.metrics_by_group.values()
        )
        results["detection_rate_threshold"] = all_detection_pass
        
        # 정확도 격차 3% 이하
        accuracies = [m.recognition_accuracy for m in report.metrics_by_group.values()]
        accuracy_disparity = max(accuracies) - min(accuracies)
        results["accuracy_disparity_threshold"] = (
            accuracy_disparity <= self.thresholds["accuracy_disparity"]
        )
        
        # FAR 기준 충족
        all_far_pass = all(
            m.false_match_rate <= self.thresholds["false_match_rate"]
            for m in report.metrics_by_group.values()
        )
        results["false_match_rate_threshold"] = all_far_pass
        
        results["overall_pass"] = all(results.values())
        
        return results
