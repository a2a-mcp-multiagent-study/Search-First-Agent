import os
import json

from dotenv import load_dotenv

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import create_react_agent

from src.agent.state import OverallState
from src.tools import get_tools
from src.prompts import get_prompt_builder

load_dotenv()


def router_node(state: OverallState):
    llm = ChatGoogleGenerativeAI(
        google_api_key=os.getenv('GOOGLE_API_KEY'),
        model="gemini-2.0-flash",
        temperature=0.65,
        model_kwargs={"response_format": "json"}
    )

    prompt_builder = get_prompt_builder("router")
    system_prompt, user_prompt = prompt_builder(state.messages[-1].content)
    
    response = llm.invoke([SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)])
    response_json = json.loads(response.content.strip().lstrip("```json").rstrip("```").replace("\'", "\""))
    
    return {
        "is_chitchat": response_json.get("category", "chitchat") == "chitchat", 
        "chitchat_rationale": response_json.get("rationale", ""),
        "messages": state.messages
    }

def rounter(state: OverallState):
    if state.is_chitchat:
        return "chitchat"
    else:
        return "investment"


def chitchat_node(state: OverallState):
    llm = ChatGoogleGenerativeAI(
        google_api_key=os.getenv('GOOGLE_API_KEY'),
        model="gemini-2.0-flash",
        temperature=0.65,
    )
        # 메시지가 5개 미만이면 전체 메시지를 사용, 그렇지 않으면 마지막 5개를 제외
    messages_to_send = state.messages[:-5] if len(state.messages) > 5 else state.messages
    
    # 빈 메시지 리스트 방지
    if not messages_to_send:
        messages_to_send = state.messages
    
    response = llm.invoke(messages_to_send)
    return {
        "messages": state.messages + [AIMessage(content=response.content)]
    }



async def build_agent():
    llm = ChatGoogleGenerativeAI(
        google_api_key=os.getenv('GOOGLE_API_KEY'),
        model="gemini-2.0-flash",
        temperature=0.65,
        model_kwargs={"response_format": "json"}
    )    
    tools = await get_tools()
    agent = create_react_agent(
        llm, 
        tools, 
        name="StockAgent",
        prompt="넌 친절한 투자 도우미야",
        state_schema=OverallState
    )
    
    
    builder = StateGraph(OverallState)

    builder.add_node("router_node", router_node)
    builder.add_node("chitchat_node", chitchat_node)
    builder.add_node("agent", agent)

    builder.add_edge(START, "router_node")
    builder.add_conditional_edges("router_node", rounter, {
        "chitchat": "chitchat_node",
        "investment": "agent"
    })
    builder.add_edge("chitchat_node", END)
    builder.add_edge("agent", END)

    
    return builder.compile()


