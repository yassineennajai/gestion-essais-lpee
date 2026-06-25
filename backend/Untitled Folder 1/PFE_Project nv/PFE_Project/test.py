import boto3
import pandas as pd
import json
import re

# ===============================
# CONFIG
# ===============================
REGION = "us-east-1"
KB_ID = "E4ZNPDMCPC"
MODEL_ID = "anthropic.claude-3-haiku-20240307-v1:0"

# ===============================
# CLIENTS
# ===============================
bedrock_runtime = boto3.client("bedrock-runtime", region_name=REGION)
agent_client = boto3.client("bedrock-agent-runtime", region_name=REGION)

# ===============================
# LOAD DATASET
# ===============================
df = pd.read_csv("Sales_Data.csv")

df["order_date"] = pd.to_datetime(df["order_date"])
df["order_year"] = df["order_date"].dt.year
df["order_month"] = df["order_date"].dt.month


# ===============================
# 1️⃣ DETECT ANALYTICS
# ===============================
def is_analytics_question(question: str):
    keywords = ["total", "sum", "average", "count", "how many", "number", "sales"]
    return any(word in question.lower() for word in keywords)


# ===============================
# 2️⃣ LLM GENERATES PANDAS CODE
# ===============================
def generate_pandas_code(question: str):

    columns = list(df.columns)

    prompt = f"""
    You are a data analyst.

    The dataframe is named df.
    Available columns: {columns}

    Generate ONLY a single valid pandas expression that answers the question.
    It must return a scalar value (number).
    Do NOT include explanations.
    Do NOT include ```python
    Only pure pandas code.

    Question: {question}
    """

    response = bedrock_runtime.invoke_model(
        modelId=MODEL_ID,
        body=json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 300,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        })
    )

    result = json.loads(response["body"].read())
    code = result["content"][0]["text"].strip()

    return code


# ===============================
# 3️⃣ SAFE EXECUTION
# ===============================
def execute_pandas_code(code: str):
    try:
        # Remove dangerous patterns
        if "import" in code or "__" in code:
            return "Unsafe code detected."

        # Safe execution environment
        safe_globals = {"df": df}
        safe_locals = {}

        result = eval(code, safe_globals, safe_locals)

        # Handle numeric results
        if isinstance(result, (int, float)):
            return f"Result: {round(result, 2)}"

        # Handle string results
        if isinstance(result, str):
            return f"Result: {result}"

        # Handle tuple / list / pandas Index
        if isinstance(result, (tuple, list, pd.Index, pd.Series)):
            # If pandas Series with values, convert to string
            if isinstance(result, pd.Series):
                if len(result) == 1:
                    result = result.iloc[0]
                else:
                    result = result.tolist()
            # Convert tuple / list to readable string
            return f"Result: {result}"

        # Catch-all fallback
        return f"Result: {result}"

    except Exception as e:
        return f"Execution error: {e}"


# ===============================
# 4️⃣ ANALYTICS HANDLER
# ===============================
def handle_analytics(question: str):

    code = generate_pandas_code(question)

    print("\n[Generated Pandas Code]:\n", code)

    return execute_pandas_code(code)


# ===============================
# 5️⃣ RAG FUNCTION
# ===============================
def ask_with_rag(question: str):

    response = agent_client.retrieve_and_generate(
        input={"text": question},
        retrieveAndGenerateConfiguration={
            "type": "KNOWLEDGE_BASE",
            "knowledgeBaseConfiguration": {
                "knowledgeBaseId": KB_ID,
                "modelArn": f"arn:aws:bedrock:{REGION}::foundation-model/{MODEL_ID}",
                "retrievalConfiguration": {
                    "vectorSearchConfiguration": {
                        "numberOfResults": 5
                    }
                }
            }
        }
    )

    return response.get("output", {}).get("text", "")


# ===============================
# MAIN LOOP
# ===============================
if __name__ == "__main__":

    print("\n🔥 Enterprise Hybrid AI Sales Agent Ready\n")

    while True:
        question = input("Ask something (type exit to stop): ")

        if question.lower() == "exit":
            break

        if is_analytics_question(question):
            print("\n[Detected type: analytics]\n")
            answer = handle_analytics(question)
        else:
            print("\n[Detected type: rag]\n")
            answer = ask_with_rag(question)

        print("\nAgent Answer:\n", answer)
        print("\n" + "-"*50 + "\n")