"""
에이전트 행동 로깅 모듈

AI Agent의 모든 행동을 구조화된 형식으로 로깅합니다.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
import json
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class AgentActionLog:
    """에이전트 행동 로그 항목"""
    timestamp: datetime
    agent_id: str
    session_id: str
    action_type: str
    action_name: str
    input_data: Any
    output_data: Any = None
    duration_ms: float = 0
    success: bool = True
    error_message: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "agent_id": self.agent_id,
            "session_id": self.session_id,
            "action_type": self.action_type,
            "action_name": self.action_name,
            "input_data": self._serialize(self.input_data),
            "output_data": self._serialize(self.output_data),
            "duration_ms": self.duration_ms,
            "success": self.success,
            "error_message": self.error_message,
            "metadata": self.metadata
        }
    
    def _serialize(self, data: Any) -> str:
        """데이터 직렬화"""
        if data is None:
            return None
        try:
            return json.dumps(data, ensure_ascii=False, default=str)[:1000]
        except:
            return str(data)[:1000]
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)


class ActionLogger:
    """
    에이전트 행동 로거
    
    다양한 출력 대상(파일, 콘솔, 원격 서버)으로 로그를 전송합니다.
    """
    
    def __init__(
        self,
        agent_id: str,
        session_id: Optional[str] = None,
        log_dir: Optional[str] = None,
        console_output: bool = True,
        file_output: bool = True
    ):
        """
        Args:
            agent_id: 에이전트 식별자
            session_id: 세션 식별자 (없으면 자동 생성)
            log_dir: 로그 디렉토리
            console_output: 콘솔 출력 여부
            file_output: 파일 출력 여부
        """
        import uuid
        
        self.agent_id = agent_id
        self.session_id = session_id or str(uuid.uuid4())[:8]
        self.console_output = console_output
        self.file_output = file_output
        
        # 로그 디렉토리 설정
        if log_dir:
            self.log_dir = Path(log_dir)
        else:
            self.log_dir = Path("logs") / "agent_actions"
        
        if self.file_output:
            self.log_dir.mkdir(parents=True, exist_ok=True)
            self._log_file = self.log_dir / f"{self.agent_id}_{self.session_id}.jsonl"
        
        self._logs: List[AgentActionLog] = []
    
    def log(
        self,
        action_type: str,
        action_name: str,
        input_data: Any,
        output_data: Any = None,
        duration_ms: float = 0,
        success: bool = True,
        error_message: str = "",
        metadata: Optional[Dict[str, Any]] = None
    ) -> AgentActionLog:
        """
        행동 로그 기록
        
        Args:
            action_type: 행동 유형 (llm_call, tool_call 등)
            action_name: 행동 이름
            input_data: 입력 데이터
            output_data: 출력 데이터
            duration_ms: 실행 시간 (밀리초)
            success: 성공 여부
            error_message: 에러 메시지
            metadata: 추가 메타데이터
        
        Returns:
            생성된 로그 항목
        """
        log_entry = AgentActionLog(
            timestamp=datetime.now(),
            agent_id=self.agent_id,
            session_id=self.session_id,
            action_type=action_type,
            action_name=action_name,
            input_data=input_data,
            output_data=output_data,
            duration_ms=duration_ms,
            success=success,
            error_message=error_message,
            metadata=metadata or {}
        )
        
        self._logs.append(log_entry)
        
        # 콘솔 출력
        if self.console_output:
            self._log_to_console(log_entry)
        
        # 파일 출력
        if self.file_output:
            self._log_to_file(log_entry)
        
        return log_entry
    
    def _log_to_console(self, log_entry: AgentActionLog):
        """콘솔에 로그 출력"""
        status = "✓" if log_entry.success else "✗"
        logger.info(
            f"[{log_entry.agent_id}] {status} {log_entry.action_type}:"
            f"{log_entry.action_name} ({log_entry.duration_ms:.0f}ms)"
        )
    
    def _log_to_file(self, log_entry: AgentActionLog):
        """파일에 로그 추가"""
        try:
            with open(self._log_file, 'a', encoding='utf-8') as f:
                f.write(log_entry.to_json() + '\n')
        except Exception as e:
            logger.error(f"로그 파일 쓰기 실패: {e}")
    
    def get_logs(
        self,
        action_type: Optional[str] = None,
        success_only: bool = False,
        limit: int = 100
    ) -> List[AgentActionLog]:
        """
        로그 조회
        
        Args:
            action_type: 행동 유형 필터
            success_only: 성공한 로그만
            limit: 최대 결과 수
        """
        logs = self._logs
        
        if action_type:
            logs = [l for l in logs if l.action_type == action_type]
        
        if success_only:
            logs = [l for l in logs if l.success]
        
        return logs[-limit:]
    
    def get_summary(self) -> Dict[str, Any]:
        """로그 요약 통계"""
        total = len(self._logs)
        success = sum(1 for l in self._logs if l.success)
        failure = total - success
        
        by_type = {}
        total_duration = 0
        
        for log in self._logs:
            by_type[log.action_type] = by_type.get(log.action_type, 0) + 1
            total_duration += log.duration_ms
        
        return {
            "agent_id": self.agent_id,
            "session_id": self.session_id,
            "total_actions": total,
            "success_count": success,
            "failure_count": failure,
            "success_rate": success / total if total > 0 else 0,
            "by_action_type": by_type,
            "total_duration_ms": total_duration,
            "avg_duration_ms": total_duration / total if total > 0 else 0
        }
    
    def export(self, filepath: str, format: str = "jsonl"):
        """
        로그 내보내기
        
        Args:
            filepath: 출력 파일 경로
            format: 출력 형식 (jsonl, json, csv)
        """
        if format == "jsonl":
            with open(filepath, 'w', encoding='utf-8') as f:
                for log in self._logs:
                    f.write(log.to_json() + '\n')
        
        elif format == "json":
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(
                    [l.to_dict() for l in self._logs],
                    f,
                    ensure_ascii=False,
                    indent=2
                )
        
        elif format == "csv":
            import csv
            
            if not self._logs:
                return
            
            fieldnames = list(self._logs[0].to_dict().keys())
            
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for log in self._logs:
                    writer.writerow(log.to_dict())
        
        logger.info(f"로그 내보내기 완료: {filepath}")
    
    def clear(self):
        """로그 초기화"""
        self._logs = []
