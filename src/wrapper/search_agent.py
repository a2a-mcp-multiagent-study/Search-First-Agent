import os
from collections.abc import AsyncIterable
from typing import Any

from dotenv import load_dotenv

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
# from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
# from langgraph.checkpoint.memory import MemorySaver
# from pydantic import BaseModel
from pydantic import BaseModel
from typing import Literal

from src.simple_agent.graph import build_agent


load_dotenv()

class ResponseFormat(BaseModel):
    """Respond to the user in this format."""

    status: Literal['input_required', 'completed', 'error'] = 'input_required'
    message: str



class SearchAgent:
    """SearchAgent - a specialized assistant for investment research and analysis."""

    def __init__(self):
        self.graph = None

    async def _get_graph(self):
        """Lazy initialization of the graph."""
        if self.graph is None:
            self.graph = await build_agent()
        return self.graph

    async def stream(self, query, context_id) -> AsyncIterable[dict[str, Any]]:
        """Stream responses from the search agent."""
        graph = await self._get_graph()
        
        inputs = {'messages': [HumanMessage(content=query)]}
        config = {'configurable': {'thread_id': context_id}}

        try:
            async for item in graph.astream(inputs, config, stream_mode='values'):
                if 'messages' in item and item['messages']:
                    message = item['messages'][-1]
                    
                    if isinstance(message, AIMessage):
                        if message.tool_calls and len(message.tool_calls) > 0:
                            yield {
                                'is_task_complete': False,
                                'require_user_input': False,
                                'content': '정보를 검색하고 분석 중입니다...',
                            }
                        else:
                            # This is likely the final response
                            yield {
                                'is_task_complete': True,
                                'require_user_input': False,
                                'content': message.content,
                            }
                            break
                    elif isinstance(message, SystemMessage):
                        yield {
                            'is_task_complete': False,
                            'require_user_input': False,
                            'content': '요청을 처리하고 있습니다...',
                        }

        except Exception as e:
            yield {
                'is_task_complete': False,
                'require_user_input': True,
                'content': f'처리 중 오류가 발생했습니다: {str(e)}',
            }


    def get_agent_response(self, config):
        current_state = self.graph.get_state(config)
        structured_response = current_state.values.get('structured_response')
        if structured_response and isinstance(
            structured_response, ResponseFormat
        ):
            if structured_response.status == 'input_required':
                return {
                    'is_task_complete': False,
                    'require_user_input': True,
                    'content': structured_response.message,
                }
            if structured_response.status == 'error':
                return {
                    'is_task_complete': False,
                    'require_user_input': True,
                    'content': structured_response.message,
                }
            if structured_response.status == 'completed':
                return {
                    'is_task_complete': True,
                    'require_user_input': False,
                    'content': structured_response.message,
                }

        return {
            'is_task_complete': False,
            'require_user_input': True,
            'content': (
                'We are unable to process your request at the moment. '
                'Please try again.'
            ),
        }

    SUPPORTED_CONTENT_TYPES = ['text', 'text/plain']
    

