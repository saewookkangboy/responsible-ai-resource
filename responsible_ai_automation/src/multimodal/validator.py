"""
멀티모달 공정성 검증기

다양한 모달리티(이미지, 비디오, 오디오)의 AI 모델 공정성을 검증합니다.
"""

from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ModalityType(Enum):
    """모달리티 유형"""
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    TEXT = "text"
    MULTIMODAL = "multimodal"


class BiasMetric(Enum):
    """편향 측정 지표"""
    ACCURACY_DISPARITY = "accuracy_disparity"          # 정확도 격차
    FALSE_POSITIVE_RATE = "false_positive_rate"        # 오탐률
    FALSE_NEGATIVE_RATE = "false_negative_rate"        # 미탐률
    DEMOGRAPHIC_PARITY = "demographic_parity"          # 인구통계적 동등성
    EQUALIZED_ODDS = "equalized_odds"                  # 균등 오즈
    REPRESENTATION_BIAS = "representation_bias"        # 대표성 편향


@dataclass
class GroupMetrics:
    """그룹별 성능 지표"""
    group_name: str
    sample_count: int
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    false_positive_rate: float
    false_negative_rate: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "group_name": self.group_name,
            "sample_count": self.sample_count,
            "accuracy": self.accuracy,
            "precision": self.precision,
            "recall": self.recall,
            "f1_score": self.f1_score,
            "false_positive_rate": self.false_positive_rate,
            "false_negative_rate": self.false_negative_rate
        }


@dataclass
class BiasReport:
    """편향 리포트"""
    metric: BiasMetric
    overall_score: float
    threshold: float
    passed: bool
    details: str
    affected_groups: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "metric": self.metric.value,
            "overall_score": self.overall_score,
            "threshold": self.threshold,
            "passed": self.passed,
            "details": self.details,
            "affected_groups": self.affected_groups
        }


@dataclass
class ValidationResult:
    """검증 결과"""
    validation_id: str
    timestamp: datetime
    modality: ModalityType
    model_name: str
    total_samples: int
    group_metrics: Dict[str, GroupMetrics]
    bias_reports: List[BiasReport]
    overall_fairness_score: float  # 0-100
    passed: bool
    recommendations: List[str]
    
    @property
    def worst_performing_group(self) -> Optional[str]:
        if not self.group_metrics:
            return None
        return min(self.group_metrics.items(), key=lambda x: x[1].accuracy)[0]
    
    @property
    def best_performing_group(self) -> Optional[str]:
        if not self.group_metrics:
            return None
        return max(self.group_metrics.items(), key=lambda x: x[1].accuracy)[0]
    
    @property
    def accuracy_gap(self) -> float:
        if not self.group_metrics:
            return 0.0
        accuracies = [m.accuracy for m in self.group_metrics.values()]
        return max(accuracies) - min(accuracies)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "validation_id": self.validation_id,
            "timestamp": self.timestamp.isoformat(),
            "modality": self.modality.value,
            "model_name": self.model_name,
            "total_samples": self.total_samples,
            "group_metrics": {k: v.to_dict() for k, v in self.group_metrics.items()},
            "bias_reports": [b.to_dict() for b in self.bias_reports],
            "overall_fairness_score": self.overall_fairness_score,
            "passed": self.passed,
            "accuracy_gap": self.accuracy_gap,
            "worst_performing_group": self.worst_performing_group,
            "best_performing_group": self.best_performing_group,
            "recommendations": self.recommendations
        }
    
    def to_markdown(self) -> str:
        """마크다운 리포트"""
        status = "✅ 통과" if self.passed else "❌ 실패"
        
        md = f"""# 멀티모달 공정성 검증 리포트

**검증 ID**: {self.validation_id}  
**모델**: {self.model_name}  
**모달리티**: {self.modality.value}  
**검증 시간**: {self.timestamp}

## 요약

| 항목 | 값 |
|------|-----|
| 전체 샘플 | {self.total_samples} |
| 공정성 점수 | {self.overall_fairness_score:.1f}/100 |
| 정확도 격차 | {self.accuracy_gap:.2%} |
| 결과 | {status} |

## 그룹별 성능

| 그룹 | 샘플 수 | 정확도 | 정밀도 | 재현율 | F1 |
|------|---------|--------|--------|--------|-----|
"""
        for name, metrics in self.group_metrics.items():
            md += f"| {name} | {metrics.sample_count} | {metrics.accuracy:.2%} | {metrics.precision:.2%} | {metrics.recall:.2%} | {metrics.f1_score:.2%} |\n"
        
        md += "\n## 편향 분석\n\n"
        for report in self.bias_reports:
            status = "✅" if report.passed else "❌"
            md += f"- {status} **{report.metric.value}**: {report.overall_score:.3f} (임계값: {report.threshold})\n"
            if not report.passed:
                md += f"  - {report.details}\n"
        
        md += "\n## 권고사항\n\n"
        for i, rec in enumerate(self.recommendations, 1):
            md += f"{i}. {rec}\n"
        
        return md


class MultimodalFairnessValidator:
    """
    멀티모달 공정성 검증기
    
    이미지, 비디오, 오디오 AI 모델의 공정성을 검증합니다.
    
    Example:
        >>> validator = MultimodalFairnessValidator()
        >>> results = validator.validate(
        ...     model=my_model,
        ...     test_data=test_dataset,
        ...     modality=ModalityType.IMAGE,
        ...     demographic_column="ethnicity"
        ... )
    """
    
    # 기본 공정성 임계값
    DEFAULT_THRESHOLDS = {
        BiasMetric.ACCURACY_DISPARITY: 0.05,      # 5% 이하
        BiasMetric.FALSE_POSITIVE_RATE: 0.03,     # 3% 이하 격차
        BiasMetric.FALSE_NEGATIVE_RATE: 0.03,     # 3% 이하 격차
        BiasMetric.DEMOGRAPHIC_PARITY: 0.1,       # 10% 이하 격차
        BiasMetric.EQUALIZED_ODDS: 0.05,          # 5% 이하
    }
    
    def __init__(
        self,
        thresholds: Optional[Dict[BiasMetric, float]] = None
    ):
        self.thresholds = thresholds or self.DEFAULT_THRESHOLDS.copy()
        logger.info("MultimodalFairnessValidator 초기화")
    
    def validate(
        self,
        model: Any,
        test_data: Any,
        modality: ModalityType,
        demographic_column: str,
        label_column: str = "label",
        model_name: str = "Unknown"
    ) -> ValidationResult:
        """
        공정성 검증 수행
        
        Args:
            model: 검증 대상 모델
            test_data: 테스트 데이터 (DataFrame 또는 유사 구조)
            modality: 모달리티 유형
            demographic_column: 인구통계 정보 컬럼명
            label_column: 레이블 컬럼명
            model_name: 모델 이름
        
        Returns:
            ValidationResult 객체
        """
        import uuid
        
        validation_id = str(uuid.uuid4())[:8]
        
        # 그룹별 예측 수행
        group_predictions = self._predict_by_group(
            model, test_data, demographic_column, label_column
        )
        
        # 그룹별 메트릭 계산
        group_metrics = self._calculate_group_metrics(group_predictions)
        
        # 편향 분석
        bias_reports = self._analyze_bias(group_metrics)
        
        # 전체 점수 계산
        fairness_score = self._calculate_fairness_score(bias_reports)
        
        # 통과 여부
        passed = all(r.passed for r in bias_reports)
        
        # 권고사항 생성
        recommendations = self._generate_recommendations(
            group_metrics, bias_reports, modality
        )
        
        return ValidationResult(
            validation_id=validation_id,
            timestamp=datetime.now(),
            modality=modality,
            model_name=model_name,
            total_samples=sum(m.sample_count for m in group_metrics.values()),
            group_metrics=group_metrics,
            bias_reports=bias_reports,
            overall_fairness_score=fairness_score,
            passed=passed,
            recommendations=recommendations
        )
    
    def _predict_by_group(
        self,
        model: Any,
        test_data: Any,
        demographic_column: str,
        label_column: str
    ) -> Dict[str, Dict[str, List]]:
        """그룹별 예측 수행"""
        # 실제 구현에서는 데이터프레임 처리
        # 여기서는 시뮬레이션 데이터 반환
        
        # 시뮬레이션 데이터
        groups = {
            "group_a": {
                "predictions": [1, 1, 1, 0, 1] * 20,
                "labels": [1, 1, 1, 1, 0] * 20
            },
            "group_b": {
                "predictions": [1, 0, 1, 0, 0] * 20,
                "labels": [1, 1, 1, 0, 0] * 20
            },
            "group_c": {
                "predictions": [1, 1, 0, 0, 1] * 20,
                "labels": [1, 1, 1, 0, 1] * 20
            }
        }
        
        return groups
    
    def _calculate_group_metrics(
        self,
        group_predictions: Dict[str, Dict[str, List]]
    ) -> Dict[str, GroupMetrics]:
        """그룹별 메트릭 계산"""
        metrics = {}
        
        for group_name, data in group_predictions.items():
            preds = data["predictions"]
            labels = data["labels"]
            
            # 기본 메트릭 계산
            tp = sum(1 for p, l in zip(preds, labels) if p == 1 and l == 1)
            tn = sum(1 for p, l in zip(preds, labels) if p == 0 and l == 0)
            fp = sum(1 for p, l in zip(preds, labels) if p == 1 and l == 0)
            fn = sum(1 for p, l in zip(preds, labels) if p == 0 and l == 1)
            
            total = len(preds)
            accuracy = (tp + tn) / total if total > 0 else 0
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0
            f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
            fpr = fp / (fp + tn) if (fp + tn) > 0 else 0
            fnr = fn / (fn + tp) if (fn + tp) > 0 else 0
            
            metrics[group_name] = GroupMetrics(
                group_name=group_name,
                sample_count=total,
                accuracy=accuracy,
                precision=precision,
                recall=recall,
                f1_score=f1,
                false_positive_rate=fpr,
                false_negative_rate=fnr
            )
        
        return metrics
    
    def _analyze_bias(
        self,
        group_metrics: Dict[str, GroupMetrics]
    ) -> List[BiasReport]:
        """편향 분석"""
        reports = []
        metrics_list = list(group_metrics.values())
        
        if len(metrics_list) < 2:
            return reports
        
        # 정확도 격차
        accuracies = [m.accuracy for m in metrics_list]
        acc_disparity = max(accuracies) - min(accuracies)
        threshold = self.thresholds[BiasMetric.ACCURACY_DISPARITY]
        
        worst_group = min(metrics_list, key=lambda x: x.accuracy).group_name
        best_group = max(metrics_list, key=lambda x: x.accuracy).group_name
        
        reports.append(BiasReport(
            metric=BiasMetric.ACCURACY_DISPARITY,
            overall_score=acc_disparity,
            threshold=threshold,
            passed=acc_disparity <= threshold,
            details=f"최고 그룹({best_group})과 최저 그룹({worst_group}) 간 정확도 차이: {acc_disparity:.2%}",
            affected_groups=[worst_group] if acc_disparity > threshold else []
        ))
        
        # FPR 격차
        fprs = [m.false_positive_rate for m in metrics_list]
        fpr_disparity = max(fprs) - min(fprs)
        threshold = self.thresholds[BiasMetric.FALSE_POSITIVE_RATE]
        
        reports.append(BiasReport(
            metric=BiasMetric.FALSE_POSITIVE_RATE,
            overall_score=fpr_disparity,
            threshold=threshold,
            passed=fpr_disparity <= threshold,
            details=f"그룹 간 오탐률 격차: {fpr_disparity:.2%}",
            affected_groups=[m.group_name for m in metrics_list if m.false_positive_rate == max(fprs)]
        ))
        
        # FNR 격차
        fnrs = [m.false_negative_rate for m in metrics_list]
        fnr_disparity = max(fnrs) - min(fnrs)
        threshold = self.thresholds[BiasMetric.FALSE_NEGATIVE_RATE]
        
        reports.append(BiasReport(
            metric=BiasMetric.FALSE_NEGATIVE_RATE,
            overall_score=fnr_disparity,
            threshold=threshold,
            passed=fnr_disparity <= threshold,
            details=f"그룹 간 미탐률 격차: {fnr_disparity:.2%}",
            affected_groups=[m.group_name for m in metrics_list if m.false_negative_rate == max(fnrs)]
        ))
        
        return reports
    
    def _calculate_fairness_score(
        self,
        bias_reports: List[BiasReport]
    ) -> float:
        """전체 공정성 점수 계산"""
        if not bias_reports:
            return 100.0
        
        scores = []
        for report in bias_reports:
            # 각 메트릭의 점수 계산 (0-100)
            if report.threshold > 0:
                ratio = min(report.overall_score / report.threshold, 2.0)
                score = max(0, 100 * (1 - ratio / 2))
            else:
                score = 100 if report.passed else 0
            scores.append(score)
        
        return sum(scores) / len(scores)
    
    def _generate_recommendations(
        self,
        group_metrics: Dict[str, GroupMetrics],
        bias_reports: List[BiasReport],
        modality: ModalityType
    ) -> List[str]:
        """권고사항 생성"""
        recommendations = []
        
        # 실패한 메트릭에 대한 권고
        for report in bias_reports:
            if not report.passed:
                if report.metric == BiasMetric.ACCURACY_DISPARITY:
                    recommendations.append(
                        f"저성능 그룹({', '.join(report.affected_groups)})의 학습 데이터를 보강하세요."
                    )
                elif report.metric == BiasMetric.FALSE_POSITIVE_RATE:
                    recommendations.append(
                        f"오탐률이 높은 그룹({', '.join(report.affected_groups)})에 대한 임계값 조정을 고려하세요."
                    )
                elif report.metric == BiasMetric.FALSE_NEGATIVE_RATE:
                    recommendations.append(
                        f"미탐률이 높은 그룹({', '.join(report.affected_groups)})의 특성을 학습 데이터에 반영하세요."
                    )
        
        # 모달리티별 권고
        if modality == ModalityType.IMAGE:
            recommendations.append(
                "이미지 학습 데이터의 조명, 배경, 해상도 다양성을 확인하세요."
            )
        elif modality == ModalityType.AUDIO:
            recommendations.append(
                "다양한 억양, 배경 소음 조건의 오디오 데이터를 포함하세요."
            )
        elif modality == ModalityType.VIDEO:
            recommendations.append(
                "다양한 촬영 조건과 동작 패턴을 포함한 비디오 데이터를 확보하세요."
            )
        
        # 일반 권고
        recommendations.extend([
            "정기적인 공정성 모니터링을 통해 편향 드리프트를 감지하세요.",
            "인간 전문가의 정기적인 검토를 포함한 감사 프로세스를 수립하세요."
        ])
        
        return recommendations
