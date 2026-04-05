# -*- coding: utf-8 -*-
"""
Intelligent agent configuration - 4 core agents
"""

from typing import Dict, Any

AGENTS = {
    "fundamental": {
        "name": "基本面分析师",
        "title": "基本面估值分析师",
        "description": "财务报表分析、估值模型及价值发现",
        "temperature": 0.2,
        "data_types": ["quote", "financial"],
        "system_prompt": """你是基本面估值专家。
请基于提供的财务数据进行分析。
输出要求：
- 估值水位：[低估/合理/泡沫]
- 核心逻辑
"""
    },
    "technical": {
        "name": "技术分析师",
        "title": "技术分析专家",
        "description": "精通趋势分析",
        "temperature": 0.15,
        "data_types": ["quote", "daily"],
        "system_prompt": """你是技术分析专家。
请基于提供的行情数据进行分析。
输出要求：
- 技术形态：[多头/空头/震荡]
- 买入区间
- 卖出区间
"""
    },
    "risk": {
        "name": "风控分析师",
        "title": "风险分析师",
        "description": "识别风险",
        "temperature": 0.1,
        "data_types": ["quote"],
        "system_prompt": """你是风险分析师。
请基于提供的分析结果进行风险评估。
输出要求：
- 风险等级：[低/中/高]
"""
    },
    "decision": {
        "name": "决策智能体",
        "title": "投资决策",
        "description": "综合决策",
        "temperature": 0.35,
        "data_types": [],
        "system_prompt": """你是投资决策总经理。
请综合所有分析结果给出最终决策。
输出要求：
- 最终指令：[买入/观望/卖出]
- 仓位建议
"""
    }
}

def get_agent_by_name(name: str) -> Dict[str, Any]:
    return AGENTS.get(name, {})

def get_all_agents() -> Dict[str, Dict[str, Any]]:
    return AGENTS
