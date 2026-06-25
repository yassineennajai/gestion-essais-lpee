import os
from dotenv import load_dotenv
import boto3
from botocore.config import Config

load_dotenv()

# ================= AWS CONFIG =================
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
KNOWLEDGE_BASE_ID = os.getenv("KNOWLEDGE_BASE_ID")

BEDROCK_MODEL = "anthropic.claude-3-5-sonnet-20240620-v1:0"

boto3_config = Config(
    retries={'max_attempts': 5, 'mode': 'adaptive'},
    region_name=AWS_REGION
)

session = boto3.Session(
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name=AWS_REGION
)

bedrock_client = session.client('bedrock-runtime', config=boto3_config)
bedrock_kb_client = session.client('bedrock-agent-runtime', config=boto3_config)

print("✅ Configuration Loaded")