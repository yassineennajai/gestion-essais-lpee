"""
CONFIGURATION MODULE
Student: [Your Name]
Course: Data Engineering 2nd Year
Project: AI Agent with Amazon Bedrock & Manus
"""

import os
from dotenv import load_dotenv
import boto3
from botocore.config import Config

# Load environment variables from .env file
load_dotenv()

# ================= AWS Configuration =================
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
KNOWLEDGE_BASE_ID = os.getenv("KNOWLEDGE_BASE_ID")

# Bedrock model selection
BEDROCK_MODEL = "anthropic.claude-3-5-sonnet-20240620-v1:0"

# Configure retry settings for AWS
boto3_config = Config(
    retries={'max_attempts': 5, 'mode': 'adaptive'},
    region_name=AWS_REGION
)

# Create AWS session
session = boto3.Session(
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name=AWS_REGION
)

# Create Bedrock clients
bedrock_client = session.client('bedrock-runtime', config=boto3_config)
bedrock_kb_client = session.client('bedrock-agent-runtime', config=boto3_config)

# ================= Manus API Configuration =================
MANUS_API_KEY = os.getenv("MANUS_API_KEY")
MANUS_API_URL = os.getenv("MANUS_API_URL")

# ================= Print configuration status =================
print("\n" + "="*50)
print("✅ CONFIGURATION LOADED SUCCESSFULLY")
print("="*50)
print(f"🌎 AWS Region: {AWS_REGION}")
print(f"📚 Knowledge Base ID: {KNOWLEDGE_BASE_ID or 'NOT CONFIGURED'}")
print(f"🤖 Bedrock Model: {BEDROCK_MODEL}")
print(f"🔑 Manus API Key: {'SET' if MANUS_API_KEY else 'NOT SET'}")
print(f"🌐 Manus API URL: {MANUS_API_URL or 'NOT SET'}")
print("="*50 + "\n")
