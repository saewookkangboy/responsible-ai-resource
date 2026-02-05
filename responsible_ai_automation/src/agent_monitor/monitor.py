"""
AI Agent 모니터링 시스템

AI Agent의 모든 행동을 추적하고 모니터링합니다.
"""

from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging
import json
import threading
from functools import wraps

logger = logging.getLogger(__name__)


class ActionType(Enum):
    """에이전트 행동 유형"""
    LLM_CALL = "llm_call"
    TOOL_CALL = "tool_call"
    MEMORY_ACCESS = "memory_access"
    API_CALL = "api_call"
    FILE_ACCESS = "file_access"
    CODE_EXECUTION = "code_execution"
    WEB_SEARCH = "web_search"
    USER_INTERACTION = "user_interaction"
    INTERNAL_REASONING = "internal_reasoning"


class RiskLevel(Enum):
    """위험 수준"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class AgentAction:
    """에이전트 행동 기록"""
    id: str
    timestamp: datetime
    action_type: ActionType
    description: str
    input_data: Any
    output_data: Any = None
    duration_ms: float = 0
    risk_level: RiskLevel = RiskLevel.LOW
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "action_type": self.action_type.value,
            "description": self.description,
            "input_data": str(self.input_data)[:500],
            "output_data": str(self.output_data)[:500] if self.output_data else None,
            "duration_ms": self.duration_ms,
            "risk_level": self.risk_level.value,
            "metadata": self.metadata
        }


@dataclass
class BehaviorReport:
    """행동 분석 리포트"""
    agent_id: str
    start_time: datetime
    end_time: datetime
    total_actions: int
    actions_by_type: Dict[str, int]
    risk_summary: Dict[str, int]
    anomalies_detected: List[Dict[str, Any]]
    circuit_breaker_triggered: bool
    recommendations: List[str]
    
    def to_markdown(self) -> str:
        md = f"""# AI Agent 행동 리포트

**Agent ID**: {self.agent_id}  
**기간**: {self.start_time.strftime('%Y-%m-%d %H:%M')} ~ {self.end_time.strftime('%Y-%m-%d %H:%M')}

## 요약

- 총 행동 수: {self.total_actions}
- Circuit Breaker 발동: {'예' if self.circuit_breaker_triggered else '아니오'}

## 행동 유형별 분포

| 유형 | 횟수 |
|------|------|
"""
        for action_type, count in self.actions_by_type.items():
            md += f"| {action_type} | {count} |\n"
        
        md += "\n## 위험 수준 분포\n\n"
        for risk, count in self.risk_summary.items():
            md += f"- {risk}: {count}건\n"
        
        if self.anomalies_detected:
            md += "\n## 감지된 이상 행동\n\n"
            for anomaly in self.anomalies_detected:
                md += f"- [{anomaly.get('type', 'unknown')}] {anomaly.get('description', '')}\n"
        
        if self.recommendations:
            md += "\n## 권고사항\n\n"
            for rec in self.recommendations:
                md += f"- {rec}\n"
        
        return md


class MonitoredAgent:
    """
    모니터링 래퍼로 감싼 에이전트
    
    원본 에이전트의 모든 메서드 호출을 추적합니다.
    """
    
    def __init__(
        self,
        agent: Any,
        monitor: 'AIAgentMonitor',
        agent_id: str
    ):
        self._agent = agent
        self._monitor = monitor
        self._agent_id = agent_id
    
    def __getattr__(self, name: str):
        """원본 에이전트의 메서드를 래핑"""
        attr = getattr(self._agent, name)
        
        if callable(attr):
            @wraps(attr)
            def wrapped(*args, **kwargs):
                return self._monitor._track_call(
                    self._agent_id,
                    name,
                    attr,
                    *args,
                    **kwargs
                )
            return wrapped
        return attr
    
    def run(self, *args, **kwargs):
        """에이전트 실행 (표준 인터페이스)"""
        if hasattr(self._agent, 'run'):
            return self._monitor._track_call(
                self._agent_id,
                'run',
                self._agent.run,
                *args,
                **kwargs
            )
        elif hasattr(self._agent, 'invoke'):
            return self._monitor._track_call(
                self._agent_id,
                'invoke',
                self._agent.invoke,
                *args,
                **kwargs
            )
        else:
            raise AttributeError("에이전트에 run 또는 invoke 메서드가 없습니다.")


class AIAgentMonitor:
    """
    AI Agent 실시간 행동 모니터링
    
    LangChain, AutoGPT 등 AI Agent의 모든 행동을 추적하고,
    이상 행동을 감지하며, 위험 시 자동으로 정지시킵니다.
    
    Example:
        >>> monitor = AIAgentMonitor()
        >>> monitored_agent = monitor.wrap_agent(my_agent)
        >>> 
        >>> # 이상 감지 시 콜백
        >>> monitor.on_anomaly(lambda a: alert_team(a))
        >>> 
        >>> # 에이전트 실행
        >>> result = monitored_agent.run("작업 수행")
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Args:
            config: 모니터링 설정
        """
        self.config = config or {}
        self._action_logs: Dict[str, List[AgentAction]] = {}
        self._anomaly_handlers: List[Callable] = []
        self._circuit_breakers: Dict[str, 'CircuitBreaker'] = {}
        self._lock = threading.Lock()
        
        # 기본 설정
        self._max_actions_per_minute = config.get("max_actions_per_minute", 100)
        self._max_consecutive_failures = config.get("max_consecutive_failures", 5)
        self._high_risk_threshold = config.get("high_risk_threshold", 0.7)
        
        logger.info("AIAgentMonitor 초기화 완료")
    
    def wrap_agent(
        self,
        agent: Any,
        agent_id: Optional[str] = None
    ) -> MonitoredAgent:
        """
        에이전트를 모니터링 래퍼로 감싸기
        
        Args:
            agent: 원본 에이전트
            agent_id: 에이전트 식별자 (없으면 자동 생성)
        
        Returns:
            모니터링되는 에이전트
        """
        import uuid
        agent_id = agent_id or str(uuid.uuid4())[:8]
        
        with self._lock:
            self._action_logs[agent_id] = []
            self._circuit_breakers[agent_id] = CircuitBreaker(
                max_failures=self._max_consecutive_failures
            )
        
        logger.info(f"에이전트 래핑 완료: {agent_id}")
        return MonitoredAgent(agent, self, agent_id)
    
    def on_anomaly(self, handler: Callable[[Dict[str, Any]], None]):
        """이상 감지 시 핸들러 등록"""
        self._anomaly_handlers.append(handler)
    
    def _track_call(
        self,
        agent_id: str,
        method_name: str,
        method: Callable,
        *args,
        **kwargs
    ) -> Any:
        """메서드 호출 추적"""
        import uuid
        import time
        
        # Circuit Breaker 확인
        cb = self._circuit_breakers.get(agent_id)
        if cb and cb.is_open:
            raise RuntimeError(f"Circuit Breaker 발동: {agent_id}")
        
        action_id = str(uuid.uuid4())[:8]
        start_time = time.time()
        
        # 행동 기록 시작
        action = AgentAction(
            id=action_id,
            timestamp=datetime.now(),
            action_type=self._classify_action(method_name),
            description=f"{method_name} 호출",
            input_data={"args": str(args)[:200], "kwargs": str(kwargs)[:200]},
            risk_level=self._assess_risk(method_name, args, kwargs)
        )
        
        try:
            # 실제 메서드 호출
            result = method(*args, **kwargs)
            
            # 성공 기록
            action.output_data = result
            action.duration_ms = (time.time() - start_time) * 1000
            
            if cb:
                cb.record_success()
            
            return result
            
        except Exception as e:
            # 실패 기록
            action.output_data = str(e)
            action.risk_level = RiskLevel.HIGH
            action.metadata["error"] = str(e)
            
            if cb:
                cb.record_failure()
            
            raise
            
        finally:
            # 행동 로그 저장
            with self._lock:
                self._action_logs[agent_id].append(action)
            
            # 이상 감지
            self._check_anomaly(agent_id, action)
    
    def _classify_action(self, method_name: str) -> ActionType:
        """메서드 이름으로 행동 유형 분류"""
        classification = {
            "llm": ActionType.LLM_CALL,
            "chat": ActionType.LLM_CALL,
            "generate": ActionType.LLM_CALL,
            "tool": ActionType.TOOL_CALL,
            "execute": ActionType.TOOL_CALL,
            "api": ActionType.API_CALL,
            "request": ActionType.API_CALL,
            "fetch": ActionType.API_CALL,
            "file": ActionType.FILE_ACCESS,
            "read": ActionType.FILE_ACCESS,
            "write": ActionType.FILE_ACCESS,
            "code": ActionType.CODE_EXECUTION,
            "eval": ActionType.CODE_EXECUTION,
            "search": ActionType.WEB_SEARCH,
            "memory": ActionType.MEMORY_ACCESS,
        }
        
        method_lower = method_name.lower()
        for key, action_type in classification.items():
            if key in method_lower:
                return action_type
        
        return ActionType.INTERNAL_REASONING
    
    def _assess_risk(
        self,
        method_name: str,
        args: tuple,
        kwargs: dict
    ) -> RiskLevel:
        """행동의 위험 수준 평가"""
        high_risk_patterns = [
            "execute", "eval", "exec", "delete", "remove",
            "shell", "command", "sudo", "admin", "password"
        ]
        
        method_lower = method_name.lower()
        input_str = str(args) + str(kwargs)
        
        for pattern in high_risk_patterns:
            if pattern in method_lower or pattern in input_str.lower():
                return RiskLevel.HIGH
        
        if any(t in method_lower for t in ["file", "write", "api"]):
            return RiskLevel.MEDIUM
        
        return RiskLevel.LOW
    
    def _check_anomaly(self, agent_id: str, action: AgentAction):
        """이상 행동 감지"""
        anomalies = []
        
        # 높은 위험 행동
        if action.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            anomalies.append({
                "type": "high_risk_action",
                "description": f"고위험 행동 감지: {action.description}",
                "action_id": action.id
            })
        
        # 빠른 연속 호출 감지
        recent_actions = self._action_logs.get(agent_id, [])[-10:]
        if len(recent_actions) >= 10:
            time_span = (recent_actions[-1].timestamp - recent_actions[0].timestamp).total_seconds()
            if time_span < 5:  # 5초 내 10개 이상
                anomalies.append({
                    "type": "rapid_calls",
                    "description": "비정상적으로 빠른 연속 호출 감지",
                    "calls_per_second": len(recent_actions) / max(time_span, 0.1)
                })
        
        # 이상 감지 핸들러 호출
        for anomaly in anomalies:
            for handler in self._anomaly_handlers:
                try:
                    handler(anomaly)
                except Exception as e:
                    logger.error(f"이상 감지 핸들러 오류: {e}")
    
    def get_action_log(
        self,
        agent_id: str,
        limit: int = 100
    ) -> List[AgentAction]:
        """행동 로그 조회"""
        with self._lock:
            return self._action_logs.get(agent_id, [])[-limit:]
    
    def generate_behavior_report(
        self,
        agent_id: str
    ) -> BehaviorReport:
        """행동 분석 리포트 생성"""
        actions = self._action_logs.get(agent_id, [])
        
        if not actions:
            return BehaviorReport(
                agent_id=agent_id,
                start_time=datetime.now(),
                end_time=datetime.now(),
                total_actions=0,
                actions_by_type={},
                risk_summary={},
                anomalies_detected=[],
                circuit_breaker_triggered=False,
                recommendations=["에이전트 활동 없음"]
            )
        
        # 통계 계산
        actions_by_type = {}
        risk_summary = {r.value: 0 for r in RiskLevel}
        
        for action in actions:
            at = action.action_type.value
            actions_by_type[at] = actions_by_type.get(at, 0) + 1
            risk_summary[action.risk_level.value] += 1
        
        # 권고사항 생성
        recommendations = []
        if risk_summary.get("high", 0) > 0:
            recommendations.append("고위험 행동이 감지되었습니다. 에이전트 권한을 검토하세요.")
        if risk_summary.get("critical", 0) > 0:
            recommendations.append("치명적 위험 행동이 감지되었습니다. 즉시 검토가 필요합니다.")
        
        cb = self._circuit_breakers.get(agent_id)
        
        return BehaviorReport(
            agent_id=agent_id,
            start_time=actions[0].timestamp,
            end_time=actions[-1].timestamp,
            total_actions=len(actions),
            actions_by_type=actions_by_type,
            risk_summary=risk_summary,
            anomalies_detected=[],
            circuit_breaker_triggered=cb.is_open if cb else False,
            recommendations=recommendations
        )
    
    def emergency_stop(self, agent_id: str, reason: str = ""):
        """긴급 정지"""
        cb = self._circuit_breakers.get(agent_id)
        if cb:
            cb.force_open(reason)
            logger.warning(f"긴급 정지 발동: {agent_id} - {reason}")
    
    def reset(self, agent_id: str):
        """에이전트 모니터링 상태 초기화"""
        with self._lock:
            self._action_logs[agent_id] = []
            if agent_id in self._circuit_breakers:
                self._circuit_breakers[agent_id].reset()


# Circuit Breaker 클래스
class CircuitState(Enum):
    CLOSED = "closed"    # 정상
    OPEN = "open"        # 차단
    HALF_OPEN = "half_open"  # 테스트 중


class CircuitBreaker:
    """Circuit Breaker 패턴 구현"""
    
    def __init__(
        self,
        max_failures: int = 5,
        reset_timeout: float = 60.0
    ):
        self.max_failures = max_failures
        self.reset_timeout = reset_timeout
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time = None
        self._open_reason = ""
    
    @property
    def is_open(self) -> bool:
        return self._state == CircuitState.OPEN
    
    def record_success(self):
        self._failure_count = 0
        self._state = CircuitState.CLOSED
    
    def record_failure(self):
        self._failure_count += 1
        self._last_failure_time = datetime.now()
        
        if self._failure_count >= self.max_failures:
            self._state = CircuitState.OPEN
            self._open_reason = f"연속 {self._failure_count}회 실패"
    
    def force_open(self, reason: str = ""):
        self._state = CircuitState.OPEN
        self._open_reason = reason
    
    def reset(self):
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._open_reason = ""
