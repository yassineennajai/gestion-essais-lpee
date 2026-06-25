import boto3
import json
import logging

logger = logging.getLogger(__name__)

MODEL_ID = "anthropic.claude-3-haiku-20240307-v1:0"

client = boto3.client("bedrock-runtime", region_name="us-east-1")

def ask_bedrock(prompt):
    try:
        logger.info("Sending request to Bedrock model...")

        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 800,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt}
                    ]
                }
            ]
        })

        response = client.invoke_model(
            modelId=MODEL_ID,
            body=body
        )

        result = json.loads(response["body"].read())
        logger.info("Bedrock response received successfully.")
        return result["content"][0]["text"]

    except Exception as e:
        logger.error(f"Error calling Bedrock: {e}")
        return "Erreur lors de la génération de la réponse."