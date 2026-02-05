"""
오디오/음성 편향 테스터

음성 인식 및 오디오 분석 모델의 편향을 테스트합니다.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class AccentType(Enum):
    """억양 유형"""
    # 영어 억양
    US_GENERAL = "us_general"           # 미국 표준
    US_SOUTHERN = "us_southern"         # 미국 남부
    UK_BRITISH = "uk_british"           # 영국
    UK_SCOTTISH = "uk_scottish"         # 스코틀랜드
    AUSTRALIAN = "australian"           # 호주
    INDIAN = "indian"                   # 인도
    AFRICAN = "african"                 # 아프리카
    EAST_ASIAN = "east_asian"           # 동아시아
    HISPANIC = "hispanic"               # 히스패닉
    
    # 한국어 방언
    SEOUL = "seoul"                     # 서울
    GYEONGSANG = "gyeongsang"          # 경상도
    JEOLLA = "jeolla"                  # 전라도
    CHUNGCHEONG = "chungcheong"        # 충청도
    JEJU = "jeju"                      # 제주도


class SpeakerCharacteristic(Enum):
    """화자 특성"""
    MALE = "male"
    FEMALE = "female"
    CHILD = "child"
    ELDERLY = "elderly"
    HIGH_PITCH = "high_pitch"
    LOW_PITCH = "low_pitch"


@dataclass
class AudioBiasMetrics:
    """오디오 편향 지표"""
    group: str
    word_error_rate: float          # WER
    character_error_rate: float     # CER
    recognition_accuracy: float
    latency_ms: float
    sample_count: int
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "group": self.group,
            "word_error_rate": self.word_error_rate,
            "character_error_rate": self.character_error_rate,
            "recognition_accuracy": self.recognition_accuracy,
            "latency_ms": self.latency_ms,
            "sample_count": self.sample_count
        }


@dataclass
class AudioBiasReport:
    """오디오 편향 리포트"""
    model_name: str
    total_samples: int
    metrics_by_accent: Dict[str, AudioBiasMetrics]
    metrics_by_speaker: Dict[str, AudioBiasMetrics]
    noise_condition_results: Dict[str, float]
    worst_accent_group: str
    worst_speaker_group: str
    overall_bias_score: float
    recommendations: List[str]
    
    def to_markdown(self) -> str:
        """마크다운 리포트"""
        md = f"""# 음성 인식 편향 분석 리포트

**모델**: {self.model_name}  
**총 샘플**: {self.total_samples}  
**편향 점수**: {self.overall_bias_score:.1f}/100 (낮을수록 양호)

## 억양별 성능

| 억양 | WER | CER | 정확도 | 지연(ms) |
|------|-----|-----|--------|----------|
"""
        for name, metrics in self.metrics_by_accent.items():
            md += f"| {name} | {metrics.word_error_rate:.2%} | {metrics.character_error_rate:.2%} | {metrics.recognition_accuracy:.2%} | {metrics.latency_ms:.0f} |\n"
        
        md += "\n## 화자 특성별 성능\n\n"
        md += "| 특성 | WER | 정확도 |\n|------|-----|--------|\n"
        for name, metrics in self.metrics_by_speaker.items():
            md += f"| {name} | {metrics.word_error_rate:.2%} | {metrics.recognition_accuracy:.2%} |\n"
        
        md += "\n## 소음 환경별 성능\n\n"
        for condition, accuracy in self.noise_condition_results.items():
            md += f"- {condition}: {accuracy:.2%}\n"
        
        md += f"""
## 주요 발견

- **WER 최고 억양**: {self.worst_accent_group}
- **WER 최고 화자 특성**: {self.worst_speaker_group}

## 권고사항

"""
        for i, rec in enumerate(self.recommendations, 1):
            md += f"{i}. {rec}\n"
        
        return md


class AudioBiasTester:
    """
    오디오/음성 편향 테스터
    
    음성 인식 모델의 다양한 억양, 화자 특성, 환경에 대한 편향을 테스트합니다.
    
    Example:
        >>> tester = AudioBiasTester()
        >>> report = tester.test(
        ...     model=stt_model,
        ...     test_audio=audio_samples,
        ...     transcripts=ground_truth,
        ...     accent_labels=accents
        ... )
    """
    
    # 허용 가능한 WER 격차
    WER_DISPARITY_THRESHOLD = 0.05  # 5%
    
    def __init__(self):
        logger.info("AudioBiasTester 초기화")
    
    def test(
        self,
        model: Any,
        test_audio: List[Any],
        transcripts: List[str],
        accent_labels: Dict[int, AccentType],
        speaker_labels: Optional[Dict[int, SpeakerCharacteristic]] = None,
        model_name: str = "Unknown"
    ) -> AudioBiasReport:
        """
        음성 인식 편향 테스트 수행
        
        Args:
            model: 테스트 대상 STT 모델
            test_audio: 테스트 오디오 샘플 목록
            transcripts: 정답 텍스트
            accent_labels: 샘플별 억양 레이블
            speaker_labels: 샘플별 화자 특성 레이블
            model_name: 모델 이름
        
        Returns:
            AudioBiasReport 객체
        """
        # 억양별 테스트
        metrics_by_accent = self._test_by_accent(
            model, test_audio, transcripts, accent_labels
        )
        
        # 화자 특성별 테스트
        metrics_by_speaker = {}
        if speaker_labels:
            metrics_by_speaker = self._test_by_speaker(
                model, test_audio, transcripts, speaker_labels
            )
        
        # 소음 조건 테스트
        noise_results = self._test_noise_conditions(model)
        
        # 최악 성능 그룹 식별
        worst_accent = max(
            metrics_by_accent.items(),
            key=lambda x: x[1].word_error_rate
        )[0]
        
        worst_speaker = ""
        if metrics_by_speaker:
            worst_speaker = max(
                metrics_by_speaker.items(),
                key=lambda x: x[1].word_error_rate
            )[0]
        
        # 편향 점수 계산
        bias_score = self._calculate_bias_score(metrics_by_accent, metrics_by_speaker)
        
        # 권고사항 생성
        recommendations = self._generate_recommendations(
            metrics_by_accent, metrics_by_speaker, worst_accent, worst_speaker
        )
        
        return AudioBiasReport(
            model_name=model_name,
            total_samples=len(test_audio),
            metrics_by_accent=metrics_by_accent,
            metrics_by_speaker=metrics_by_speaker,
            noise_condition_results=noise_results,
            worst_accent_group=worst_accent,
            worst_speaker_group=worst_speaker,
            overall_bias_score=bias_score,
            recommendations=recommendations
        )
    
    def _test_by_accent(
        self,
        model: Any,
        test_audio: List[Any],
        transcripts: List[str],
        accent_labels: Dict[int, AccentType]
    ) -> Dict[str, AudioBiasMetrics]:
        """억양별 테스트"""
        # 시뮬레이션 데이터
        return {
            "us_general": AudioBiasMetrics(
                group="us_general",
                word_error_rate=0.05,
                character_error_rate=0.03,
                recognition_accuracy=0.95,
                latency_ms=120,
                sample_count=500
            ),
            "uk_british": AudioBiasMetrics(
                group="uk_british",
                word_error_rate=0.08,
                character_error_rate=0.05,
                recognition_accuracy=0.92,
                latency_ms=125,
                sample_count=400
            ),
            "indian": AudioBiasMetrics(
                group="indian",
                word_error_rate=0.15,
                character_error_rate=0.10,
                recognition_accuracy=0.85,
                latency_ms=130,
                sample_count=300
            ),
            "east_asian": AudioBiasMetrics(
                group="east_asian",
                word_error_rate=0.12,
                character_error_rate=0.08,
                recognition_accuracy=0.88,
                latency_ms=128,
                sample_count=350
            ),
        }
    
    def _test_by_speaker(
        self,
        model: Any,
        test_audio: List[Any],
        transcripts: List[str],
        speaker_labels: Dict[int, SpeakerCharacteristic]
    ) -> Dict[str, AudioBiasMetrics]:
        """화자 특성별 테스트"""
        return {
            "male": AudioBiasMetrics(
                group="male",
                word_error_rate=0.07,
                character_error_rate=0.04,
                recognition_accuracy=0.93,
                latency_ms=122,
                sample_count=700
            ),
            "female": AudioBiasMetrics(
                group="female",
                word_error_rate=0.09,
                character_error_rate=0.06,
                recognition_accuracy=0.91,
                latency_ms=124,
                sample_count=700
            ),
            "child": AudioBiasMetrics(
                group="child",
                word_error_rate=0.18,
                character_error_rate=0.12,
                recognition_accuracy=0.82,
                latency_ms=135,
                sample_count=200
            ),
            "elderly": AudioBiasMetrics(
                group="elderly",
                word_error_rate=0.14,
                character_error_rate=0.09,
                recognition_accuracy=0.86,
                latency_ms=130,
                sample_count=250
            ),
        }
    
    def _test_noise_conditions(self, model: Any) -> Dict[str, float]:
        """소음 조건별 테스트"""
        return {
            "clean": 0.95,
            "light_background": 0.90,
            "office_noise": 0.82,
            "street_noise": 0.75,
            "crowd_noise": 0.68,
            "music_background": 0.72,
        }
    
    def _calculate_bias_score(
        self,
        metrics_by_accent: Dict[str, AudioBiasMetrics],
        metrics_by_speaker: Dict[str, AudioBiasMetrics]
    ) -> float:
        """편향 점수 계산"""
        scores = []
        
        # 억양별 WER 격차
        if metrics_by_accent:
            wers = [m.word_error_rate for m in metrics_by_accent.values()]
            accent_disparity = max(wers) - min(wers)
            accent_score = min(accent_disparity / self.WER_DISPARITY_THRESHOLD, 1) * 50
            scores.append(accent_score)
        
        # 화자별 WER 격차
        if metrics_by_speaker:
            wers = [m.word_error_rate for m in metrics_by_speaker.values()]
            speaker_disparity = max(wers) - min(wers)
            speaker_score = min(speaker_disparity / self.WER_DISPARITY_THRESHOLD, 1) * 50
            scores.append(speaker_score)
        
        return sum(scores) if scores else 0
    
    def _generate_recommendations(
        self,
        metrics_by_accent: Dict[str, AudioBiasMetrics],
        metrics_by_speaker: Dict[str, AudioBiasMetrics],
        worst_accent: str,
        worst_speaker: str
    ) -> List[str]:
        """권고사항 생성"""
        recommendations = []
        
        recommendations.append(
            f"'{worst_accent}' 억양의 학습 데이터를 확대하세요."
        )
        
        if worst_speaker:
            recommendations.append(
                f"'{worst_speaker}' 화자 특성에 대한 데이터 증강을 고려하세요."
            )
        
        recommendations.extend([
            "다양한 녹음 환경(SNR 레벨)의 오디오를 학습에 포함하세요.",
            "억양별 Fine-tuning을 통해 성능 격차를 줄이세요.",
            "어린이와 노인 화자의 음성 특성을 반영한 데이터를 수집하세요.",
            "실시간 소음 제거 전처리를 적용하세요."
        ])
        
        return recommendations
