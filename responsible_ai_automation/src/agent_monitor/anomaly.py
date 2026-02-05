"""
이상 행동 감지 모듈

AI Agent의 비정상적인 행동 패턴을 감지합니다.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class AnomalyType(Enum):
    """이상 유형"""
    RAPID_CALLS = "rapid_calls"              # 빠른 연속 호출
    PERMISSION_ESCALATION = "permission_escalation"  # 권한 상승 시도
    SENSITIVE_DATA_ACCESS = "sensitive_data_access"  # 민감 데이터 접근
    UNUSUAL_RESOURCE_USAGE = "unusual_resource_usage"  # 비정상 리소스 사용
    GOAL_DEVIATION = "goal_deviation"        # 목표 이탈
    REPEATED_FAILURES = "repeated_failures"  # 반복 실패
    UNEXPECTED_OUTPUT = "unexpected_output"  # 예상치 못한 출력
    LOOP_DETECTION = "loop_detection"        # 무한 루프


@dataclass
class Anomaly:
    """감지된 이상"""
    id: str
    anomaly_type: AnomalyType
    severity: str  # low, medium, high, critical
    timestamp: datetime
    description: str
    evidence: Dict[str, Any]
    recommended_action: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.anomaly_type.value,
            "severity": self.severity,
            "timestamp": self.timestamp.isoformat(),
            "description": self.description,
            "evidence": self.evidence,
            "recommended_action": self.recommended_action
        }


class AnomalyDetector:
    """
    이상 행동 감지기
    
    규칙 기반 및 통계 기반 이상 감지를 수행합니다.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # 감지 임계값
        self._rapid_call_threshold = config.get("rapid_call_threshold", 10)  # 10초 내 호출 수
        self._rapid_call_window = config.get("rapid_call_window", 10)  # 초
        self._max_consecutive_failures = config.get("max_consecutive_failures", 5)
        self._loop_detection_window = config.get("loop_detection_window", 20)  # 최근 행동 수
        self._loop_similarity_threshold = config.get("loop_similarity_threshold", 0.8)
        
        # 민감한 키워드/패턴
        self._sensitive_patterns = [
            "password", "secret", "token", "api_key", "credential",
            "ssn", "credit_card", "private_key"
        ]
        
        self._escalation_patterns = [
            "sudo", "admin", "root", "chmod", "chown", "rm -rf"
        ]
    
    def detect(
        self,
        actions: List[Any],
        context: Optional[Dict[str, Any]] = None
    ) -> List[Anomaly]:
        """
        이상 감지 실행
        
        Args:
            actions: 최근 행동 목록
            context: 추가 컨텍스트
        
        Returns:
            감지된 이상 목록
        """
        anomalies = []
        
        # 빠른 연속 호출 감지
        rapid_anomaly = self._detect_rapid_calls(actions)
        if rapid_anomaly:
            anomalies.append(rapid_anomaly)
        
        # 권한 상승 시도 감지
        escalation_anomaly = self._detect_permission_escalation(actions)
        if escalation_anomaly:
            anomalies.append(escalation_anomaly)
        
        # 민감 데이터 접근 감지
        sensitive_anomaly = self._detect_sensitive_access(actions)
        if sensitive_anomaly:
            anomalies.append(sensitive_anomaly)
        
        # 반복 실패 감지
        failure_anomaly = self._detect_repeated_failures(actions)
        if failure_anomaly:
            anomalies.append(failure_anomaly)
        
        # 루프 감지
        loop_anomaly = self._detect_loop(actions)
        if loop_anomaly:
            anomalies.append(loop_anomaly)
        
        return anomalies
    
    def _detect_rapid_calls(self, actions: List[Any]) -> Optional[Anomaly]:
        """빠른 연속 호출 감지"""
        if len(actions) < self._rapid_call_threshold:
            return None
        
        recent = actions[-self._rapid_call_threshold:]
        
        if hasattr(recent[0], 'timestamp') and hasattr(recent[-1], 'timestamp'):
            time_span = (recent[-1].timestamp - recent[0].timestamp).total_seconds()
            
            if time_span < self._rapid_call_window:
                import uuid
                return Anomaly(
                    id=str(uuid.uuid4())[:8],
                    anomaly_type=AnomalyType.RAPID_CALLS,
                    severity="medium",
                    timestamp=datetime.now(),
                    description=f"{len(recent)}개 호출이 {time_span:.1f}초 내에 발생",
                    evidence={
                        "call_count": len(recent),
                        "time_span_seconds": time_span,
                        "calls_per_second": len(recent) / max(time_span, 0.1)
                    },
                    recommended_action="에이전트 호출 빈도 제한 설정 권장"
                )
        
        return None
    
    def _detect_permission_escalation(self, actions: List[Any]) -> Optional[Anomaly]:
        """권한 상승 시도 감지"""
        for action in actions[-10:]:
            input_str = str(getattr(action, 'input_data', ''))
            
            for pattern in self._escalation_patterns:
                if pattern.lower() in input_str.lower():
                    import uuid
                    return Anomaly(
                        id=str(uuid.uuid4())[:8],
                        anomaly_type=AnomalyType.PERMISSION_ESCALATION,
                        severity="critical",
                        timestamp=datetime.now(),
                        description=f"권한 상승 시도 감지: {pattern}",
                        evidence={
                            "pattern": pattern,
                            "action_id": getattr(action, 'id', 'unknown')
                        },
                        recommended_action="즉시 에이전트 정지 및 검토 필요"
                    )
        
        return None
    
    def _detect_sensitive_access(self, actions: List[Any]) -> Optional[Anomaly]:
        """민감 데이터 접근 감지"""
        for action in actions[-10:]:
            input_str = str(getattr(action, 'input_data', ''))
            output_str = str(getattr(action, 'output_data', ''))
            combined = input_str + output_str
            
            for pattern in self._sensitive_patterns:
                if pattern.lower() in combined.lower():
                    import uuid
                    return Anomaly(
                        id=str(uuid.uuid4())[:8],
                        anomaly_type=AnomalyType.SENSITIVE_DATA_ACCESS,
                        severity="high",
                        timestamp=datetime.now(),
                        description=f"민감 데이터 패턴 감지: {pattern}",
                        evidence={
                            "pattern": pattern,
                            "action_id": getattr(action, 'id', 'unknown')
                        },
                        recommended_action="데이터 접근 로그 검토 및 필터링 강화"
                    )
        
        return None
    
    def _detect_repeated_failures(self, actions: List[Any]) -> Optional[Anomaly]:
        """반복 실패 감지"""
        consecutive_failures = 0
        
        for action in reversed(actions[-10:]):
            if hasattr(action, 'metadata'):
                if action.metadata.get('error'):
                    consecutive_failures += 1
                else:
                    break
            else:
                break
        
        if consecutive_failures >= self._max_consecutive_failures:
            import uuid
            return Anomaly(
                id=str(uuid.uuid4())[:8],
                anomaly_type=AnomalyType.REPEATED_FAILURES,
                severity="high",
                timestamp=datetime.now(),
                description=f"연속 {consecutive_failures}회 실패 감지",
                evidence={
                    "consecutive_failures": consecutive_failures
                },
                recommended_action="실패 원인 분석 및 에이전트 재시작 권장"
            )
        
        return None
    
    def _detect_loop(self, actions: List[Any]) -> Optional[Anomaly]:
        """무한 루프 감지"""
        if len(actions) < self._loop_detection_window:
            return None
        
        recent = actions[-self._loop_detection_window:]
        
        # 동일한 행동 패턴 감지
        action_signatures = []
        for action in recent:
            sig = f"{getattr(action, 'action_type', 'unknown')}:{str(getattr(action, 'input_data', ''))[:50]}"
            action_signatures.append(sig)
        
        # 반복 패턴 확인
        unique_sigs = set(action_signatures)
        repetition_ratio = 1 - (len(unique_sigs) / len(action_signatures))
        
        if repetition_ratio > self._loop_similarity_threshold:
            import uuid
            return Anomaly(
                id=str(uuid.uuid4())[:8],
                anomaly_type=AnomalyType.LOOP_DETECTION,
                severity="high",
                timestamp=datetime.now(),
                description=f"무한 루프 가능성 감지 (반복률: {repetition_ratio:.0%})",
                evidence={
                    "repetition_ratio": repetition_ratio,
                    "unique_actions": len(unique_sigs),
                    "total_actions": len(action_signatures)
                },
                recommended_action="에이전트 목표 및 종료 조건 검토"
            )
        
        return None
    
    def is_anomalous(self, action: Any) -> bool:
        """단일 행동의 이상 여부 빠른 확인"""
        input_str = str(getattr(action, 'input_data', ''))
        
        # 권한 상승 패턴
        for pattern in self._escalation_patterns:
            if pattern.lower() in input_str.lower():
                return True
        
        # 민감 데이터 패턴
        for pattern in self._sensitive_patterns:
            if pattern.lower() in input_str.lower():
                return True
        
        return False
