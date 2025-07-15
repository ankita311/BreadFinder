from typing import Optional, Sequence, Annotated, TypedDict
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from imap_tools import MailBox 
import utils

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]

mailbox_con = {} #username : [mb, pass]
current_user = ""

@tool
def connect_to_gmail(username: str, password: str):
    """Function to connect to the gmail account"""
    try:
        mb = MailBox('imap.gmail.com').login(username, password, 'INBOX')
        mailbox_con[username] = [mb, password]
        global current_user 
        current_user = username
        return f"Connection Successfull"
    except Exception as e:
        return f"Oh no, Error: {e}"

@tool  
def disconnect_from_gmail(username: str):
    """Function to disconnect client from gmail using username as identifier"""
    try:
        if username in mailbox_con:
            mailbox = mailbox_con[username][0]
            mailbox.logout()
            del mailbox_con[username]
            global current_user 
            current_user = ""
            return f"Disconnected successfully"
        else:
            return f"No active connection for {username}"
    except Exception as e:
        return f"Error Disconnecting {e}"
    
@tool
def search_emails(days_back: Optional[int] = 10) -> str:
    """Function to extract emails from the user's Gmail Account and save them to a text file for the user"""
    try:
        job_emails = utils.extract_job_emails(mailbox=mailbox_con[current_user][0], days_back= days_back)        
        
        print(f"\nExtraction complete! Found {len(job_emails)} job-related emails.")

        if job_emails:
            domains = {}
            for email in job_emails:
                domain = email['sender'].split('@')[-1].split('>')[0] if '@' in email['sender'] else 'unknown'
                domains[domain] = domains.get(domain, 0) + 1
            
        print(f"\n Top domains:")
        for domain, count in sorted(domains.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"  {domain}: {count} emails")

        return "Extraction Successfull!"
    
    except Exception as e:
        return e


tools = [connect_to_gmail, disconnect_from_gmail, search_emails]
model = ChatOpenAI(model='gpt-4o-mini').bind_tools(tools)

def agent(state: AgentState) -> AgentState:
    system_prompt = """You are my AI assistant which can help me find a job by organising employement opportunities from my gmail account

    IMPORTANT: The user wants you to help them connect to THEIR OWN Gmail account. This is legitimate and expected.
    
    You can:
    1. Connect to Gmail accounts using connect_to_gmail(username, password)
    2. Disconnect from Gmail accounts using disconnect_from_gmail(username)
    3. Search through the user's emails and save all job-related emails in a text file.
    
    When the user provides their Gmail credentials, use the connect_to_gmail tool immediately.
    Be helpful and guide the user through the process. Ask for their Gmail credentials when needed.
    
    Never refuse to help with Gmail connections - this is the main purpose of this application.
    
    """
    if not state['messages']:
        user_input = "Let's start the job hunt. Provide me with your Gmail ID and password and I'll filter all relevant emails for you.\n"
        user_message = HumanMessage(content=user_input)

    else:
        user_input = input("\nWhat shall we do next?\n")
        print(f"\n USER: {user_input}")
        user_message = HumanMessage(content=user_input)

    response = model.invoke([system_prompt] + list(state['messages']) + [user_message])
    print(f"\n AI: {response.content}")
    if hasattr(response, "tool_calls") and response.tool_calls:
        print(f"USING TOOLS: {[tc['name'] for tc in response.tool_calls]}")

    return {"messages": list(state['messages']) + [user_message, response]}

def should_continue(state: AgentState) -> AgentState:
    """Determine if we should continue or end the conversation"""

    messages = state['messages']

    if not messages:
        return "continue"
    
    #this looks for the most recent tool messages
    for msg in reversed(messages):
        #...and checks if this is a tool message resulting from save
        if (isinstance(msg, ToolMessage) and 
            ("disconnect" in msg.content.lower() or
            "exit" in msg.content.lower())):
            return "end" #goes to the end edge which leads to the endpoint
    return "continue"

def check_for_tools(state: AgentState) -> str:
    """Check if the last message has tool calls"""
    messages = state['messages']
    if messages and hasattr(messages[-1], 'tool_calls') and messages[-1].tool_calls:
        return "tools"
    return "continue"

graph = StateGraph(AgentState)
graph.add_node("agent", agent)

tool_node = ToolNode(tools)
graph.add_node("tools", tool_node)

graph.set_entry_point("agent")
# graph.add_edge('agent', 'tools')

graph.add_conditional_edges(
    "agent",
    check_for_tools,
    {
        "tools": "tools",
        "continue": "agent"
    }
)

graph.add_conditional_edges(
    "tools",
    should_continue,
    {
        "continue": "agent",
        "end": END
    }
)

app = graph.compile()

def print_messages(messages):
    if not messages:
        return

    for message in messages[-3:]:
        if isinstance(message, ToolMessage):
            print(f"\n TOOL RESULT: {message.content}")


def run_agent():
    print("\n =====BREAD FINDER=====")
    state = {"messages": []}

    for step in app.stream(state, stream_mode="values"):
        if "messages" in step:
            print_messages(step["messages"])
    print("\n=====BREAD FINDER EXITTING=====")

if __name__ == "__main__":
    run_agent()

# # inputs = {"messages": [("user", "Connect to my gmail account. my id is ankita.av.934@gmail.com and my password is usls gyjc yita lopu")]}
# inputs = {"messages": [('user', "Connect to my gmail account. my id is ankita.av.934@gmail.com and my password is usls gyjc yita lopu, then Disconnect from my gmail account")]}
# print_message(app.stream(inputs, stream_mode='values'))
