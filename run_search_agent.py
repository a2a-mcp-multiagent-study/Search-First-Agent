#!/usr/bin/env python3
"""
Search-First Investment Research Agent를 A2A 프로토콜로 실행하는 스크립트
"""

import logging
import os
import sys

import httpx
import uvicorn

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import (
    BasePushNotificationSender,
    InMemoryPushNotificationConfigStore,
    InMemoryTaskStore,
)
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
)
from dotenv import load_dotenv

from src.wrapper.search_agent import SearchAgent
from src.wrapper.search_agent_executor import SearchAgentExecutor


load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Starts the Search-First Investment Research Agent server."""
    host = os.getenv('HOST', 'localhost')
    port = int(os.getenv('PORT', '10001'))
    
    try:
        capabilities = AgentCapabilities(streaming=True, push_notifications=True)
        
        skill = AgentSkill(
            id='investment_research',
            name='Investment Research and Analysis Tool',
            description='Helps with stock analysis, market research, and investment decisions',
            tags=['investment research', 'stock analysis', 'market research', 'financial analysis'],
            examples=['삼성전자 주가 분석해줘', '테슬라 실적은 어때?', '시장 전망이 궁금해'],
        )
        
        agent_card = AgentCard(
            name='Search-First Investment Research Agent',
            description='투자 연구 및 분석을 위한 전문 AI 어시스턴트',
            url=f'http://{host}:{port}/',
            version='1.0.0',
            default_input_modes=SearchAgent.SUPPORTED_CONTENT_TYPES,
            default_output_modes=SearchAgent.SUPPORTED_CONTENT_TYPES,
            capabilities=capabilities,
            skills=[skill],
        )

        # --8<-- [start:DefaultRequestHandler]
        httpx_client = httpx.AsyncClient()
        push_config_store = InMemoryPushNotificationConfigStore()
        
        push_sender = BasePushNotificationSender(httpx_client=httpx_client,
                        config_store=push_config_store)
        
        request_handler = DefaultRequestHandler(
            agent_executor=SearchAgentExecutor(),
            task_store=InMemoryTaskStore(),
            push_config_store=push_config_store,
            push_sender=push_sender
        )
        
        server = A2AStarletteApplication(
            agent_card=agent_card, http_handler=request_handler
        )

        logger.info(f"Starting Search-First Investment Research Agent on {host}:{port}")
        
        uvicorn.run(server.build(), host=host, port=port)
        # --8<-- [end:DefaultRequestHandler]

    except Exception as e:
        logger.error(f'An error occurred during server startup: {e}')
        sys.exit(1)


if __name__ == '__main__':
    main()
