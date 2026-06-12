import json
import uuid
import os
from langsmith import Client, evaluate
from langchain_google_genai import ChatGoogleGenerativeAI

# Set up environment variables if not loaded
from dotenv import load_dotenv
load_dotenv()

from app.agent import root_agent

client = Client()

# 1. Load Data
print("Loading dataset...")
with open("app/eval_set_1.evalset.json", "r") as f:
    eval_data = json.load(f)

dataset_name = "Checkout Promo Evals"
if client.has_dataset(dataset_name=dataset_name):
    client.delete_dataset(dataset_name=dataset_name)

dataset = client.create_dataset(dataset_name=dataset_name)

# 2. Upload Examples
print("Uploading examples to LangSmith...")
for case in eval_data["eval_cases"]:
    # Extract the first turn from the conversation
    first_turn = case["conversation"][0]
    input_text = first_turn["user_content"]["parts"][0]["text"]
    expected_output = first_turn["final_response"]["parts"][0]["text"]
    
    client.create_example(
        inputs={"input": input_text},
        outputs={"expected": expected_output},
        dataset_id=dataset.id,
    )

from app.langsmith_agent import agent as lg_agent

import asyncio

# 3. Define the Target Agent
def target_agent(inputs: dict):
    # Use a fresh session for each evaluation run to ensure isolation
    session_id = str(uuid.uuid4())
    print(f"Running agent for input: {inputs['input'][:50]}...")
    
    # LangGraph wrapped agents expect dictionaries for messages
    response = asyncio.run(
        lg_agent.ainvoke(
            {"messages": [{"role": "user", "content": inputs["input"]}]}, 
            config={"configurable": {"thread_id": session_id}}
        )
    )
    
    # The final message from the agent is at the end of the messages list
    final_message = response["messages"][-1].content
    return {"output": final_message}

from langchain_google_genai import ChatGoogleGenerativeAI

# 4. Define Evaluators
eval_llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash", temperature=0)

def qa_evaluator(run, example):
    # LLM-as-a-judge to evaluate the quality of the response
    agent_output = str(run.outputs.get("output", ""))
    expected = str(example.outputs.get("expected", ""))
    
    prompt = f"""
    You are an expert grading a customer support agent.
    
    EXPECTED IDEAL RESPONSE:
    {expected}
    
    ACTUAL AGENT RESPONSE:
    {agent_output}
    
    Does the actual response contain the same critical information and successfully complete the task shown in the expected response? 
    Respond with exactly "YES" or "NO".
    """
    
    try:
        result = eval_llm.invoke(prompt)
        score = 1 if "YES" in result.content else 0
    except Exception as e:
        print(f"Eval error: {e}")
        score = 0
    return {"key": "qa_correctness", "score": score}

def exact_match_evaluator(run, example):
    # Heuristic check to see if the final total is correct
    agent_output = str(run.outputs.get("output", ""))
    score = 1 if "269.98" in agent_output else 0
    return {"key": "calculated_correct_total", "score": score}

print("Starting evaluation suite...")
results = evaluate(
    target_agent,
    data=dataset_name,
    evaluators=[qa_evaluator, exact_match_evaluator],
    experiment_prefix="checkout-promo-v1",
)
print("\\nEvaluation complete! View results in the LangSmith dashboard.")
