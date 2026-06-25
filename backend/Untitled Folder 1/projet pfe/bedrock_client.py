import boto3
import json

client = boto3.client("bedrock-runtime", region_name="us-east-1")

MODEL_ID = "anthropic.claude-3-5-sonnet-20240620-v1:0"


def ask_claude(message, max_tokens=300):

    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": max_tokens,
        "messages": [
            {"role": "user", "content": message}
        ]
    }

    res = client.invoke_model(
        modelId=MODEL_ID,
        contentType="application/json",
        accept="application/json",
        body=json.dumps(body)
    )

    result = json.loads(res["body"].read())

    return result["content"][0]["text"]
