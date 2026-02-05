"""
리포트 시각화 모듈

평가 결과를 다양한 차트와 그래프로 시각화합니다.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import json


class ChartType(Enum):
    """차트 유형"""
    RADAR = "radar"
    GAUGE = "gauge"
    BAR = "bar"
    LINE = "line"
    HEATMAP = "heatmap"
    PIE = "pie"
    TABLE = "table"


@dataclass
class ChartConfig:
    """차트 설정"""
    chart_type: ChartType
    title: str
    data: Dict[str, Any]
    options: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.chart_type.value,
            "title": self.title,
            "data": self.data,
            "options": self.options or {}
        }


class ReportVisualizer:
    """
    리포트 시각화 생성기
    
    평가 결과를 다양한 시각적 형태로 변환합니다.
    """
    
    def __init__(self):
        self._charts: List[ChartConfig] = []
    
    def create_radar_chart(
        self,
        metrics: Dict[str, float],
        title: str = "RAI 메트릭 개요"
    ) -> ChartConfig:
        """
        레이더 차트 생성 (공정성, 투명성 등 다차원 메트릭)
        
        Args:
            metrics: 메트릭명과 값의 딕셔너리
            title: 차트 제목
        
        Returns:
            ChartConfig 객체
        """
        chart = ChartConfig(
            chart_type=ChartType.RADAR,
            title=title,
            data={
                "labels": list(metrics.keys()),
                "datasets": [{
                    "label": "현재 점수",
                    "data": list(metrics.values()),
                    "backgroundColor": "rgba(54, 162, 235, 0.2)",
                    "borderColor": "rgb(54, 162, 235)"
                }]
            },
            options={
                "scales": {
                    "r": {
                        "min": 0,
                        "max": 1
                    }
                }
            }
        )
        self._charts.append(chart)
        return chart
    
    def create_gauge_chart(
        self,
        value: float,
        title: str = "전체 RAI 점수",
        thresholds: Optional[Dict[str, float]] = None
    ) -> ChartConfig:
        """
        게이지 차트 생성 (전체 점수 표시)
        
        Args:
            value: 현재 값 (0-1)
            title: 차트 제목
            thresholds: 임계값 설정 {"good": 0.8, "warning": 0.6, "danger": 0.4}
        
        Returns:
            ChartConfig 객체
        """
        if thresholds is None:
            thresholds = {"good": 0.8, "warning": 0.6, "danger": 0.4}
        
        # 색상 결정
        if value >= thresholds["good"]:
            color = "#4CAF50"  # 녹색
        elif value >= thresholds["warning"]:
            color = "#FFC107"  # 노란색
        else:
            color = "#F44336"  # 빨간색
        
        chart = ChartConfig(
            chart_type=ChartType.GAUGE,
            title=title,
            data={
                "value": value,
                "min": 0,
                "max": 1,
                "color": color
            },
            options={
                "thresholds": thresholds,
                "format": "{value:.0%}"
            }
        )
        self._charts.append(chart)
        return chart
    
    def create_bar_chart(
        self,
        categories: List[str],
        values: List[float],
        title: str = "메트릭 비교",
        threshold: Optional[float] = None
    ) -> ChartConfig:
        """
        바 차트 생성
        
        Args:
            categories: 카테고리 목록
            values: 값 목록
            title: 차트 제목
            threshold: 임계값 표시선
        
        Returns:
            ChartConfig 객체
        """
        colors = [
            "#4CAF50" if v >= (threshold or 0.7) else "#F44336"
            for v in values
        ]
        
        chart = ChartConfig(
            chart_type=ChartType.BAR,
            title=title,
            data={
                "labels": categories,
                "datasets": [{
                    "label": "점수",
                    "data": values,
                    "backgroundColor": colors
                }]
            },
            options={
                "threshold": threshold,
                "indexAxis": "y"
            }
        )
        self._charts.append(chart)
        return chart
    
    def create_heatmap(
        self,
        matrix: List[List[float]],
        row_labels: List[str],
        col_labels: List[str],
        title: str = "상관관계 히트맵"
    ) -> ChartConfig:
        """
        히트맵 생성 (상관관계, 혼동 행렬 등)
        
        Args:
            matrix: 2D 매트릭스 데이터
            row_labels: 행 레이블
            col_labels: 열 레이블
            title: 차트 제목
        
        Returns:
            ChartConfig 객체
        """
        chart = ChartConfig(
            chart_type=ChartType.HEATMAP,
            title=title,
            data={
                "matrix": matrix,
                "rowLabels": row_labels,
                "colLabels": col_labels
            },
            options={
                "colorScale": ["#F44336", "#FFEB3B", "#4CAF50"],
                "showValues": True
            }
        )
        self._charts.append(chart)
        return chart
    
    def create_comparison_table(
        self,
        data: List[Dict[str, Any]],
        columns: List[str],
        title: str = "메트릭 비교 테이블"
    ) -> ChartConfig:
        """
        비교 테이블 생성
        
        Args:
            data: 테이블 데이터
            columns: 컬럼 정의
            title: 테이블 제목
        
        Returns:
            ChartConfig 객체
        """
        chart = ChartConfig(
            chart_type=ChartType.TABLE,
            title=title,
            data={
                "rows": data,
                "columns": columns
            },
            options={
                "sortable": True,
                "highlightThreshold": True
            }
        )
        self._charts.append(chart)
        return chart
    
    def create_trend_chart(
        self,
        timestamps: List[str],
        metrics: Dict[str, List[float]],
        title: str = "시간별 추이"
    ) -> ChartConfig:
        """
        시계열 트렌드 차트 생성
        
        Args:
            timestamps: 시간 레이블
            metrics: 메트릭별 시계열 데이터
            title: 차트 제목
        
        Returns:
            ChartConfig 객체
        """
        datasets = []
        colors = ["#2196F3", "#4CAF50", "#FFC107", "#F44336", "#9C27B0"]
        
        for i, (metric_name, values) in enumerate(metrics.items()):
            datasets.append({
                "label": metric_name,
                "data": values,
                "borderColor": colors[i % len(colors)],
                "fill": False
            })
        
        chart = ChartConfig(
            chart_type=ChartType.LINE,
            title=title,
            data={
                "labels": timestamps,
                "datasets": datasets
            },
            options={
                "responsive": True,
                "maintainAspectRatio": True
            }
        )
        self._charts.append(chart)
        return chart
    
    def get_all_charts(self) -> List[Dict[str, Any]]:
        """모든 차트 데이터 반환"""
        return [chart.to_dict() for chart in self._charts]
    
    def clear(self):
        """차트 목록 초기화"""
        self._charts = []
    
    def to_html(self) -> str:
        """HTML 시각화 코드 생성"""
        charts_json = json.dumps(self.get_all_charts(), ensure_ascii=False)
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        .chart-container {{
            width: 100%;
            max-width: 600px;
            margin: 20px auto;
        }}
    </style>
</head>
<body>
    <div id="charts"></div>
    <script>
        const chartsData = {charts_json};
        // Chart.js 렌더링 로직
        chartsData.forEach((chartConfig, index) => {{
            const container = document.createElement('div');
            container.className = 'chart-container';
            container.innerHTML = `<h3>${{chartConfig.title}}</h3><canvas id="chart-${{index}}"></canvas>`;
            document.getElementById('charts').appendChild(container);
            
            // 실제 Chart.js 렌더링은 차트 타입에 따라 구현
        }});
    </script>
</body>
</html>
"""
        return html
