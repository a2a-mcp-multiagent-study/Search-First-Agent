import os
import json

from dotenv import load_dotenv

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import create_react_agent

from src.simple_agent.state import OverallState
from src.tools import get_tools
from src.prompts import get_prompt_builder, DEFAULT_SYSTEM_PROMPT


tools_by_name = {}
load_dotenv()


def router_node(state: OverallState):
    llm = ChatOpenAI(
        model=os.getenv('GROQ_MODEL_NAME'),
        openai_api_key=os.getenv('GROQ_API_KEY', 'EMPTY'),
        openai_api_base=os.getenv('GROQ_API_URL'),
        temperature=0.65,
    )
    llm.bind(response_format={"type": "json_object"})

    prompt_builder = get_prompt_builder("router")
    system_prompt, user_prompt = prompt_builder(state.messages[-1].content)
    
    response = llm.invoke([SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)])
    response_json = json.loads(response.content.strip().lstrip("```json").rstrip("```").replace("\'", "\""))
    
    return {
        "is_chitchat": response_json.get("category", "chitchat") == "chitchat", 
        "chitchat_rationale": response_json.get("rationale", ""),
        "messages": state.messages
    }


def router(state: OverallState):
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



async def build_agent():
    
    llm = ChatOpenAI(
        model=os.getenv('GROQ_MODEL_NAME'),
        openai_api_key=os.getenv('GROQ_API_KEY', 'EMPTY'),
        openai_api_base=os.getenv('GROQ_API_URL'),
        temperature=0.65
    )

    tools = await get_tools()
    llm.bind_tools(tools)
    
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
    builder.add_node("search_agent", search_agent)
    
    builder.add_edge(START, "router_node")
    builder.add_conditional_edges("router_node", router, {
        "chitchat": "chitchat_node",
        "investment": "search_agent"
    })
    builder.add_edge("chitchat_node", END)
    builder.add_edge("search_agent", END)
    

    return builder.compile()

