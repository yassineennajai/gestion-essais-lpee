from manus import Task, Workflow
from app import ask_with_rag, call_lambda_analytics, parse_question_with_llm

# Task: Parse question
def parse_question_task(question, session_id=None):
    return parse_question_with_llm(question, session_id)

# Task: Analytics
def analytics_task(parsed):
    if parsed.get("type") == "analytics":
        return call_lambda_analytics(parsed)
    return None

# Task: RAG
def rag_task(question):
    return ask_with_rag(question)

# Define Workflow
agent_workflow = Workflow(name="SalesAgentWorkflow")

# Step 1: Parse question
agent_workflow.add_task(Task(parse_question_task, name="parse_question"))

# Step 2: Route based on type
def route_task(results, question):
    parsed = results["parse_question"]
    if parsed.get("type") == "analytics":
        return analytics_task(parsed)
    else:
        return rag_task(question)

agent_workflow.add_task(Task(route_task, name="route_task"))