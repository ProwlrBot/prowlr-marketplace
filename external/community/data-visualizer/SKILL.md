---
name: data-visualizer
description: Use this skill when the user wants to create charts, graphs, or dashboards from data — bar charts, line charts, scatter plots, heatmaps, or multi-panel dashboards.
---

# Data Visualizer

## Overview

Generate publication-quality charts and interactive dashboards from data using matplotlib (static PNG/SVG) or Plotly (interactive HTML). Includes AI-powered chart type selection.

## Chart Type Selector

```python
import anthropic
import json

client = anthropic.Anthropic()

def recommend_chart_type(data_description: str, goal: str) -> dict:
    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=256,
        tools=[{
            "name": "chart_recommendation",
            "description": "Recommend the best chart type",
            "input_schema": {
                "type": "object",
                "properties": {
                    "chart_type": {"type": "string", "enum": ["bar", "line", "scatter", "pie", "heatmap", "histogram", "box", "area"]},
                    "reason": {"type": "string"},
                    "x_axis": {"type": "string"},
                    "y_axis": {"type": "string"}
                },
                "required": ["chart_type", "reason"]
            }
        }],
        tool_choice={"type": "tool", "name": "chart_recommendation"},
        messages=[{"role": "user", "content": f"Data: {data_description}\nGoal: {goal}\nRecommend the best chart type."}],
    )
    for block in response.content:
        if block.type == "tool_use":
            return block.input
    return {"chart_type": "bar"}
```

## Matplotlib Charts

```python
import matplotlib.pyplot as plt
import matplotlib.style as mplstyle
import pandas as pd
from pathlib import Path

mplstyle.use('seaborn-v0_8-whitegrid')
COLORS = ["#2563EB", "#10B981", "#F59E0B", "#EF4444", "#8B5CF6"]

def bar_chart(data: dict, title: str, xlabel: str, ylabel: str,
              output_path: str = "chart.png") -> str:
    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.bar(data.keys(), data.values(), color=COLORS[:len(data)])

    # Add value labels on bars
    for bar in bars:
        ax.text(bar.get_x() + bar.get_width()/2., bar.get_height(),
                f'{bar.get_height():.1f}', ha='center', va='bottom', fontsize=10)

    ax.set_title(title, fontsize=14, fontweight='bold', pad=15)
    ax.set_xlabel(xlabel, fontsize=11)
    ax.set_ylabel(ylabel, fontsize=11)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    return output_path

def line_chart(df: pd.DataFrame, x_col: str, y_cols: list[str],
               title: str, output_path: str = "chart.png") -> str:
    fig, ax = plt.subplots(figsize=(12, 6))
    for i, col in enumerate(y_cols):
        ax.plot(df[x_col], df[col], label=col, color=COLORS[i % len(COLORS)], linewidth=2)

    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.legend()
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    return output_path
```

## Interactive Plotly Dashboard

```python
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def create_dashboard(metrics: dict, title: str, output_path: str = "dashboard.html") -> str:
    """Create a multi-panel interactive dashboard."""
    n = len(metrics)
    cols = min(n, 2)
    rows = (n + cols - 1) // cols

    fig = make_subplots(rows=rows, cols=cols,
                         subplot_titles=list(metrics.keys()))

    for i, (metric_name, data) in enumerate(metrics.items()):
        row = i // cols + 1
        col = i % cols + 1
        fig.add_trace(
            go.Scatter(x=list(range(len(data))), y=data,
                       name=metric_name, mode='lines+markers'),
            row=row, col=col
        )

    fig.update_layout(
        title_text=title,
        height=400 * rows,
        showlegend=False,
    )
    fig.write_html(output_path)
    return output_path
```

## Quick Reference

| Chart | Function | Library |
|-------|----------|---------|
| Bar chart | `bar_chart(data, ...)` | matplotlib |
| Line chart | `line_chart(df, ...)` | matplotlib |
| Dashboard | `create_dashboard(metrics, ...)` | plotly |
| Heatmap | `px.imshow(df)` | plotly express |
| Histogram | `ax.hist(data, bins=30)` | matplotlib |
