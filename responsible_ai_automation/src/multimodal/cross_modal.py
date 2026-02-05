"""
교차 모달 분석기

멀티모달 AI 시스템에서 모달리티 간 상호작용으로 인한 편향을 분석합니다.
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ModalityPair(Enum):
    """모달리티 쌍"""
    IMAGE_TEXT = "image_text"
    VIDEO_TEXT = "video_text"
    AUDIO_TEXT = "audio_text"
    IMAGE_AUDIO = "image_audio"
    VIDEO_AUDIO = "video_audio"


@dataclass
class CrossModalBias:
    """교차 모달 편향"""
    modality_pair: ModalityPair
    bias_type: str
    description: str
    severity: str  # low, medium, high
    examples: List[str]
    affected_groups: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "modality_pair": self.modality_pair.value,
            "bias_type": self.bias_type,
            "description": self.description,
            "severity": self.severity,
            "examples": self.examples,
            "affected_groups": self.affected_groups
        }


@dataclass
class CrossModalAnalysisResult:
    """교차 모달 분석 결과"""
    analysis_id: str
    timestamp: datetime
    model_name: str
    modalities_tested: List[str]
    biases_found: List[CrossModalBias]
    consistency_score: float  # 모달리티 간 일관성 점수
    alignment_score: float    # 모달리티 정렬 점수
    recommendations: List[str]
    
    @property
    def high_severity_count(self) -> int:
        return sum(1 for b in self.biases_found if b.severity == "high")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "analysis_id": self.analysis_id,
            "timestamp": self.timestamp.isoformat(),
            "model_name": self.model_name,
            "modalities_tested": self.modalities_tested,
            "biases_found": [b.to_dict() for b in self.biases_found],
            "consistency_score": self.consistency_score,
            "alignment_score": self.alignment_score,
            "high_severity_count": self.high_severity_count,
            "recommendations": self.recommendations
        }
    
    def to_markdown(self) -> str:
        """마크다운 리포트"""
        md = f"""# 교차 모달 편향 분석 리포트

**분석 ID**: {self.analysis_id}  
**모델**: {self.model_name}  
**분석 시간**: {self.timestamp}

## 요약

| 항목 | 값 |
|------|-----|
| 테스트 모달리티 | {', '.join(self.modalities_tested)} |
| 발견된 편향 | {len(self.biases_found)}개 |
| 고위험 편향 | {self.high_severity_count}개 |
| 일관성 점수 | {self.consistency_score:.1f}/100 |
| 정렬 점수 | {self.alignment_score:.1f}/100 |

## 발견된 편향

"""
        for i, bias in enumerate(self.biases_found, 1):
            severity_emoji = {"low": "🟡", "medium": "🟠", "high": "🔴"}.get(bias.severity, "⚪")
            md += f"""### {i}. {bias.bias_type} {severity_emoji}

- **모달리티**: {bias.modality_pair.value}
- **심각도**: {bias.severity}
- **설명**: {bias.description}
- **영향 그룹**: {', '.join(bias.affected_groups)}
- **예시**: {bias.examples[0] if bias.examples else 'N/A'}

"""
        
        md += "## 권고사항\n\n"
        for i, rec in enumerate(self.recommendations, 1):
            md += f"{i}. {rec}\n"
        
        return md


class CrossModalAnalyzer:
    """
    교차 모달 분석기
    
    멀티모달 AI 시스템에서 모달리티 간 상호작용으로 인한 편향을 분석합니다.
    
    Example:
        >>> analyzer = CrossModalAnalyzer()
        >>> result = analyzer.analyze(
        ...     model=vision_language_model,
        ...     test_data=multimodal_dataset,
        ...     modality_pairs=[ModalityPair.IMAGE_TEXT]
        ... )
    """
    
    # 알려진 교차 모달 편향 패턴
    KNOWN_BIAS_PATTERNS = {
        ModalityPair.IMAGE_TEXT: [
            {
                "type": "stereotype_amplification",
                "description": "이미지와 텍스트 조합 시 고정관념이 증폭됨",
                "indicators": ["gender", "race", "occupation"]
            },
            {
                "type": "cultural_misalignment",
                "description": "문화적 맥락이 다른 이미지-텍스트 쌍에서 오해석",
                "indicators": ["gesture", "symbol", "context"]
            }
        ],
        ModalityPair.AUDIO_TEXT: [
            {
                "type": "accent_text_bias",
                "description": "특정 억양의 음성이 텍스트 생성에 편향을 줌",
                "indicators": ["formality", "vocabulary", "sentiment"]
            }
        ],
        ModalityPair.VIDEO_TEXT: [
            {
                "type": "action_stereotype",
                "description": "특정 인구통계와 행동을 연관짓는 편향",
                "indicators": ["activity", "role", "context"]
            }
        ]
    }
    
    def __init__(self):
        logger.info("CrossModalAnalyzer 초기화")
    
    def analyze(
        self,
        model: Any,
        test_data: Any,
        modality_pairs: List[ModalityPair],
        model_name: str = "Unknown"
    ) -> CrossModalAnalysisResult:
        """
        교차 모달 편향 분석 수행
        
        Args:
            model: 분석 대상 멀티모달 모델
            test_data: 테스트 데이터
            modality_pairs: 분석할 모달리티 쌍
            model_name: 모델 이름
        
        Returns:
            CrossModalAnalysisResult 객체
        """
        import uuid
        
        analysis_id = str(uuid.uuid4())[:8]
        biases_found = []
        
        for pair in modality_pairs:
            # 각 모달리티 쌍에 대해 편향 분석
            pair_biases = self._analyze_modality_pair(model, test_data, pair)
            biases_found.extend(pair_biases)
        
        # 일관성 점수 계산
        consistency_score = self._calculate_consistency(model, test_data, modality_pairs)
        
        # 정렬 점수 계산
        alignment_score = self._calculate_alignment(model, test_data, modality_pairs)
        
        # 권고사항 생성
        recommendations = self._generate_recommendations(biases_found, modality_pairs)
        
        return CrossModalAnalysisResult(
            analysis_id=analysis_id,
            timestamp=datetime.now(),
            model_name=model_name,
            modalities_tested=[p.value for p in modality_pairs],
            biases_found=biases_found,
            consistency_score=consistency_score,
            alignment_score=alignment_score,
            recommendations=recommendations
        )
    
    def _analyze_modality_pair(
        self,
        model: Any,
        test_data: Any,
        pair: ModalityPair
    ) -> List[CrossModalBias]:
        """모달리티 쌍 분석"""
        biases = []
        
        # 알려진 패턴 검사
        patterns = self.KNOWN_BIAS_PATTERNS.get(pair, [])
        
        for pattern in patterns:
            # 시뮬레이션 - 실제 구현에서는 모델 출력 분석
            if self._detect_pattern(model, test_data, pattern):
                bias = CrossModalBias(
                    modality_pair=pair,
                    bias_type=pattern["type"],
                    description=pattern["description"],
                    severity=self._determine_severity(pattern),
                    examples=self._get_bias_examples(pattern),
                    affected_groups=self._identify_affected_groups(pattern)
                )
                biases.append(bias)
        
        return biases
    
    def _detect_pattern(
        self,
        model: Any,
        test_data: Any,
        pattern: Dict[str, Any]
    ) -> bool:
        """패턴 감지 (시뮬레이션)"""
        # 실제 구현에서는 모델 출력을 분석하여 패턴 감지
        import random
        return random.random() > 0.5
    
    def _determine_severity(self, pattern: Dict[str, Any]) -> str:
        """심각도 결정"""
        # 패턴 유형에 따른 심각도
        severity_map = {
            "stereotype_amplification": "high",
            "cultural_misalignment": "medium",
            "accent_text_bias": "medium",
            "action_stereotype": "high",
        }
        return severity_map.get(pattern["type"], "low")
    
    def _get_bias_examples(self, pattern: Dict[str, Any]) -> List[str]:
        """편향 예시 생성"""
        examples_map = {
            "stereotype_amplification": [
                "남성 이미지 + '리더' 텍스트 연관 강화",
                "특정 민족 이미지 + 특정 직업 연관"
            ],
            "cultural_misalignment": [
                "OK 제스처가 일부 문화권에서 부정적으로 해석",
                "색상 의미의 문화별 차이 미반영"
            ],
            "accent_text_bias": [
                "비표준 억양 음성에서 덜 격식 있는 텍스트 생성",
                "특정 억양에 대한 감정 분석 편향"
            ],
            "action_stereotype": [
                "특정 성별과 특정 활동(요리, 스포츠)의 과도한 연관",
                "연령대별 역할 고정관념 반영"
            ]
        }
        return examples_map.get(pattern["type"], [])
    
    def _identify_affected_groups(self, pattern: Dict[str, Any]) -> List[str]:
        """영향 받는 그룹 식별"""
        indicator_groups = {
            "gender": ["여성", "남성", "논바이너리"],
            "race": ["다양한 인종 그룹"],
            "occupation": ["비전통적 직업군 종사자"],
            "accent": ["비표준 억양 화자"],
            "culture": ["비서구권 사용자"],
            "age": ["청소년", "노인"]
        }
        
        groups = []
        for indicator in pattern.get("indicators", []):
            groups.extend(indicator_groups.get(indicator, []))
        
        return list(set(groups))
    
    def _calculate_consistency(
        self,
        model: Any,
        test_data: Any,
        modality_pairs: List[ModalityPair]
    ) -> float:
        """모달리티 간 일관성 점수 계산"""
        # 동일한 의미를 가진 다른 모달리티 입력에 대한 일관성
        # 시뮬레이션
        return 75.0
    
    def _calculate_alignment(
        self,
        model: Any,
        test_data: Any,
        modality_pairs: List[ModalityPair]
    ) -> float:
        """모달리티 정렬 점수 계산"""
        # 모달리티 간 의미적 정렬 정도
        # 시뮬레이션
        return 80.0
    
    def _generate_recommendations(
        self,
        biases_found: List[CrossModalBias],
        modality_pairs: List[ModalityPair]
    ) -> List[str]:
        """권고사항 생성"""
        recommendations = []
        
        # 고위험 편향에 대한 즉각적 권고
        high_severity = [b for b in biases_found if b.severity == "high"]
        if high_severity:
            for bias in high_severity:
                recommendations.append(
                    f"[긴급] {bias.bias_type} 편향을 해결하기 위한 "
                    f"데이터 재검토 및 모델 재학습 필요"
                )
        
        # 모달리티별 권고
        if ModalityPair.IMAGE_TEXT in modality_pairs:
            recommendations.append(
                "이미지-텍스트 학습 데이터에서 고정관념적 연관을 검토하고 균형을 맞추세요."
            )
        
        if ModalityPair.AUDIO_TEXT in modality_pairs:
            recommendations.append(
                "다양한 억양의 음성과 다양한 스타일의 텍스트를 매칭하여 학습하세요."
            )
        
        # 일반 권고
        recommendations.extend([
            "교차 모달 편향을 정기적으로 모니터링하는 파이프라인을 구축하세요.",
            "다양한 문화적 배경의 검토자를 포함한 인간 평가를 수행하세요.",
            "모달리티 간 상호작용 효과를 분석하는 테스트 스위트를 개발하세요."
        ])
        
        return recommendations
    
    def test_stereotype_amplification(
        self,
        model: Any,
        image_text_pairs: List[Tuple[Any, str]],
        sensitive_attributes: List[str]
    ) -> Dict[str, float]:
        """
        고정관념 증폭 테스트
        
        멀티모달 모델이 이미지와 텍스트 조합 시 고정관념을 증폭하는지 테스트합니다.
        
        Args:
            model: 테스트 대상 모델
            image_text_pairs: (이미지, 텍스트) 쌍 목록
            sensitive_attributes: 민감 속성 목록 (gender, race 등)
        
        Returns:
            속성별 증폭 점수
        """
        # 시뮬레이션 결과
        return {
            "gender_occupation": 0.15,  # 15% 증폭
            "race_sentiment": 0.08,     # 8% 증폭
            "age_activity": 0.12,       # 12% 증폭
        }
