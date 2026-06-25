import json
from config import bedrock_client, bedrock_kb_client, BEDROCK_MODEL, KNOWLEDGE_BASE_ID

# ================= GENERAL LLM =================
def ask_general(question):

    request_body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 800,
        "temperature": 0.7,
        "messages": [
            {
                "role": "user",
                "content": [{"type": "text", "text": question}]
            }
        ]
    }

    response = bedrock_client.invoke_model(
        modelId=BEDROCK_MODEL,
        contentType="application/json",
        body=json.dumps(request_body)
    )

    response_body = json.loads(response['body'].read())
    return response_body['content'][0]['text']


# ================= KNOWLEDGE BASE (RAG) =================
def ask_company_data(question):

    if not KNOWLEDGE_BASE_ID:
        return "Knowledge Base not configured."

    response = bedrock_kb_client.retrieve_and_generate(
        input={'text': question},
        retrieveAndGenerateConfiguration={
            'type': 'KNOWLEDGE_BASE',
            'knowledgeBaseConfiguration': {
                'knowledgeBaseId': KNOWLEDGE_BASE_ID,
                'modelArn': f'arn:aws:bedrock:{bedrock_client.meta.region_name}::foundation-model/{BEDROCK_MODEL}',
                'retrievalConfiguration': {
                    'vectorSearchConfiguration': {
                        'numberOfResults': 25,
                        'overrideSearchType': 'HYBRID'
                    }
                }
            }
        }
    )

    return response['output']['text']