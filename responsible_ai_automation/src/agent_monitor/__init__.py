"""
AI Agent 행동 모니터링 모듈

LangChain, AutoGPT 등 자율 AI Agent의 행동을 실시간으로 추적하고 이상 행동을 감지합니다.

주요 기능:
- 실시간 행동 추적 및 로깅
- 이상 행동 감지 (Anomaly Detection)
- Circuit Breaker (긴급 정지)
- 행동 감사 및 리포트

사용 예시:
    from src.agent_monitor import AIAgentMonitor, MonitoredAgent
    
    monitor = AIAgentMonitor()
    monitored_agent = monitor.wrap_agent(my_langchain_agent)
    
    # 에이전트 실행
    result = monitored_agent.run("작업 수행")
    
    # 행동 리포트 조회
    report = monitor.generate_behavior_report()
"""

from .monitor import AIAgentMonitor, MonitoredAgent
from .anomaly import AnomalyDetector, AnomalyType
from .circuit_breaker import CircuitBreaker, CircuitState
from .logging import AgentActionLog, ActionLogger

__all__ = [
    "AIAgentMonitor",
    "MonitoredAgent",
    "AnomalyDetector",
    "AnomalyType",
    "CircuitBreaker",
    "CircuitState",
    "AgentActionLog",
    "ActionLogger",
]

__version__ = "0.1.0"
