import os
import json

from dotenv import load_dotenv

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import InMemorySaver
from prompts import DEFAULT_SYSTEM_PROMPT

from src.agent.state import OverallState
from src.tools import get_tools
from src.prompts import get_prompt_builder

tools_by_name = {}
load_dotenv()


def router_node(state: OverallState):
    llm = ChatGoogleGenerativeAI(
        google_api_key=os.getenv('GOOGLE_API_KEY'),
        model="gemini-2.0-flash",
        temperature=0.0,
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
    """
    Chitchat node is a node that handles small talk.
    Not supporting multi-turn conversation.
    """
    llm = ChatGoogleGenerativeAI(
        google_api_key=os.getenv('GOOGLE_API_KEY'),
        model="gemini-2.0-flash",
        temperature=0.65,
    )
    
    chitchat_prompt_builder = get_prompt_builder("chitchat")
    system_prompt, user_prompt = chitchat_prompt_builder(state.messages[-1].content)
    response = llm.invoke([SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)])
    
    return {
        "messages": state.messages + [AIMessage(content=response.content)]
    }


def search_planner_node(state: OverallState):
    llm = ChatGoogleGenerativeAI(
        google_api_key=os.getenv('GOOGLE_API_KEY'),
        model="gemini-2.0-flash",
        temperature=0.65,
    )
    
    search_planner_prompt_builder = get_prompt_builder("planner")
    system_prompt, user_prompt = search_planner_prompt_builder(state.messages[-1].content)
    response = llm.invoke([SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)])
    
    response_json = json.loads(response.content.strip().lstrip("```json").rstrip("```").replace("\'", "\""))
    
    return {
        "search_plan": response_json,
        "messages": state.messages
    }


def aggregator_node(state: OverallState):
    llm = ChatGoogleGenerativeAI(
        google_api_key=os.getenv('GOOGLE_API_KEY'),
        model="gemini-2.0-flash",
        temperature=0.65,
    )
    
    search_planner_prompt_builder = get_prompt_builder("planner")
    system_prompt, user_prompt = search_planner_prompt_builder(state.messages[-1].content)
    response = llm.invoke([SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)])
    
    response_json = json.loads(response.content.strip().lstrip("```json").rstrip("```").replace("\'", "\""))
    
    return {
        "search_plan": response_json,
        "messages": state.messages
    }


async def build_agent():
    llm = ChatGoogleGenerativeAI(
        google_api_key=os.getenv('GOOGLE_API_KEY'),
        model="gemini-2.0-flash",
        temperature=0.65,
        model_kwargs={"response_format": "json"}
    )    
    tools = await get_tools()
    
    # memory = InMemorySaver()
    search_agent = create_react_agent(
        llm, 
        tools, 
        name="StockAgent",
        prompt=DEFAULT_SYSTEM_PROMPT,
        state_schema=OverallState
    )    
    
    builder = StateGraph(OverallState)

    builder.add_node("router_node", router_node)
    builder.add_node("chitchat_node", chitchat_node)
    builder.add_node("search_planner_node", search_planner_node)
    builder.add_node("search_agent", search_agent)
    builder.add_node("aggregator_node", aggregator_node)
    
    builder.add_edge(START, "router_node")
    builder.add_conditional_edges("router_node", rounter, {
        "chitchat": "chitchat_node",
        "investment": "search_planner_node"
    })
    builder.add_edge("chitchat_node", END)
    builder.add_edge("search_planner_node", "search_agent")
    builder.add_edge("search_agent", "aggregator_node")
    builder.add_edge("aggregator_node", END)
    

    return builder.compile()


