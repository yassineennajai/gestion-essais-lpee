"""
BEDROCK CLIENT MODULE
Student: [Your Name]

This file handles all interactions with Amazon Bedrock:
- General questions use the standard Bedrock API
- Company questions use the Knowledge Base API with enhanced prompts
- Smart routing decides which one to use
"""

import json
import re
from config import bedrock_client, bedrock_kb_client, BEDROCK_MODEL, KNOWLEDGE_BASE_ID

def ask_general(question):
    """
    Handle general questions using Bedrock directly.
    Used for non-company questions like "What is machine learning?"
    """
    print(f"\n🤔 General question: {question[:50]}...")
    
    try:
        # Prepare request for Claude
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
        
        # Call Bedrock API
        response = bedrock_client.invoke_model(
            modelId=BEDROCK_MODEL,
            contentType="application/json",
            body=json.dumps(request_body)
        )
        
        # Parse response
        response_body = json.loads(response['body'].read())
        answer = response_body['content'][0]['text']
        
        return answer
        
    except Exception as e:
        print(f"❌ Error in ask_general: {str(e)}")
        return f"Sorry, I encountered an error: {str(e)}"


def create_sales_prompt(question):
    """
    Create an enhanced prompt for sales-related questions.
    This forces the LLM to look at ALL records and sum them properly.
    """
    # Extract state from question if present
    state = "California"  # default
    if 'california' in question.lower() or 'ca' in question.lower():
        state = "California"
    elif 'texas' in question.lower() or 'tx' in question.lower():
        state = "Texas"
    elif 'new york' in question.lower() or 'ny' in question.lower():
        state = "New York"
    
    prompt = f"""I need you to calculate the EXACT TOTAL sales amount for {state}.

Original question: {question}

⚠️ **CRITICAL INSTRUCTIONS - READ CAREFULLY:**
1. You have been given MULTIPLE sales records in the retrieved documents
2. Your task is to FIND ALL sales records for {state} and ADD THEM TOGETHER
3. Do NOT just pick one record - you must SUM all of them
4. If you see 5 records, add all 5. If you see 50 records, add all 50.
5. Show your work step by step

📊 **Follow this exact format:**

SALES RECORDS FOUND IN {state.upper()}:
----------------------------------------
[List each sales amount you find]

CALCULATION:
----------------------------------------
[Show the addition: amount1 + amount2 + amount3 + ... = total]

RESULTS:
----------------------------------------
✅ **Total Sales: $[SUM OF ALL RECORDS]**
📈 Number of Transactions: [COUNT]
💰 Average Transaction: $[AVERAGE]

⚠️ **IMPORTANT:** Double-check that you included ALL records. If you only found a few records, tell me how many you found and note that there might be more in the database.
"""
    return prompt


def create_general_kb_prompt(question):
    """
    Create a general prompt for non-sales knowledge base questions.
    """
    prompt = f"""Please answer this question based on the company documents provided.

Question: {question}

Instructions:
1. Use ONLY the information from the retrieved documents
2. If the information isn't in the documents, say so
3. Be concise but complete in your answer
4. Cite which documents you used if possible

Answer:"""
    return prompt


def ask_company_data(question):
    """
    Handle questions about company data using Knowledge Base.
    Uses enhanced prompts for better results.
    """
    print(f"\n📚 Company data question: {question[:50]}...")
    
    try:
        # Validate Knowledge Base ID
        if not KNOWLEDGE_BASE_ID:
            return "❌ Knowledge Base not configured. Please check your .env file."
        
        # Detect question type
        question_lower = question.lower()
        is_sales_question = any(word in question_lower for word in 
                               ['sales', 'revenue', 'total', 'sum', 'amount'])
        is_california = 'california' in question_lower or 'ca' in question_lower
        
        # Choose prompt and retrieval settings based on question type
        if is_sales_question and is_california:
            print("💰 SALES QUESTION DETECTED - Using enhanced aggregation prompt")
            enhanced_question = create_sales_prompt(question)
            num_results = 100  # Get maximum documents for sales
            print(f"🔍 Retrieving up to {num_results} documents for accurate total")
        else:
            print("📋 General knowledge base question")
            enhanced_question = create_general_kb_prompt(question)
            num_results = 25  # Standard for other questions
        
        # Query the Knowledge Base
        response = bedrock_kb_client.retrieve_and_generate(
            input={'text': enhanced_question},
            retrieveAndGenerateConfiguration={
                'type': 'KNOWLEDGE_BASE',
                'knowledgeBaseConfiguration': {
                    'knowledgeBaseId': KNOWLEDGE_BASE_ID,
                    'modelArn': f'arn:aws:bedrock:{bedrock_client.meta.region_name}::foundation-model/{BEDROCK_MODEL}',
                    'retrievalConfiguration': {
                        'vectorSearchConfiguration': {
                            'numberOfResults': num_results,  # Critical setting!
                            'overrideSearchType': 'HYBRID'  # Better search quality
                        }
                    }
                }
            }
        )
        
        # Get the answer
        answer = response['output']['text']
        
        # Count how many documents were actually retrieved
        citations = response.get('citations', [])
        doc_count = 0
        for citation in citations:
            doc_count += len(citation.get('retrievedReferences', []))
        
        print(f"📊 Retrieved {doc_count} documents from knowledge base")
        
        # Add verification note for sales questions
        if is_sales_question and is_california:
            if doc_count < 10:
                answer += f"\n\n⚠️ **NOTE: I only found {doc_count} sales records. The actual total in your database might be higher.**"
            else:
                answer += f"\n\n✅ **Verified: This total comes from {doc_count} sales records.**"
        
        return answer
        
    except Exception as e:
        print(f"❌ Error in ask_company_data: {str(e)}")
        return f"Error accessing company data: {str(e)}"


def route_question(question):
    """
    Decide which function to use based on the question content.
    Simple but effective routing logic.
    """
    if not question:
        return "Please ask a question."
    
    q = question.lower()
    
    # Company data keywords - expanded list
    company_keywords = [
        # Sales and revenue
        'sales', 'revenue', 'profit', 'earnings',
        'customer', 'order', 'transaction',
        
        # Locations
        'california', 'texas', 'york', 'florida', 'state',
        'region', 'location', 'branch',
        
        # Calculations
        'total', 'sum', 'amount', 'average', 'minimum', 'maximum',
        
        # Company information
        'company', 'our', 'employee', 'staff', 'hr', 'policy',
        'benefit', 'vacation', 'sick', 'leave',
        
        # Products and inventory
        'product', 'inventory', 'stock', 'price', 'cost',
        'item', 'sku', 'category'
    ]
    
    # Check each keyword
    for keyword in company_keywords:
        if keyword in q:
            print(f"🔍 Detected company keyword: '{keyword}'")
            print("📋 Routing to Knowledge Base")
            return ask_company_data(question)
    
    # If no company keywords found
    print("💬 No company keywords detected - using general knowledge")
    return ask_general(question)


# Diagnostic function to test knowledge base
def test_knowledge_base():
    """
    Simple test to verify knowledge base is working.
    Call this function to debug issues.
    """
    print("\n🔧 RUNNING KNOWLEDGE BASE DIAGNOSTIC")
    print("="*50)
    
    test_questions = [
        "Show me some sales records",
        "What data do you have about California?",
        "List available information"
    ]
    
    for q in test_questions:
        print(f"\n📝 Testing: {q}")
        result = ask_company_data(q)
        print(f"Result preview: {result[:200]}...")
        print("-"*30)