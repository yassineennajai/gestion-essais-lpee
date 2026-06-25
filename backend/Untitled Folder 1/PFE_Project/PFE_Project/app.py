"""
MAIN APPLICATION
Student: [Your Name]
Course: Data Engineering 2nd Year

Simple Flask web app that provides a chat interface for the AI agent.
"""

from flask import Flask, request, jsonify, render_template
from bedrock_client import route_question, test_knowledge_base
from datetime import datetime
import os

# Create Flask app
app = Flask(__name__)

@app.route('/')
def home():
    """Serve the chat interface"""
    return render_template('index.html')

@app.route('/ask', methods=['POST'])
def ask():
    """
    API endpoint that processes questions
    Expects: JSON with {'question': 'user question'}
    Returns: JSON with {'answer': 'response', 'time': 'timestamp'}
    """
    try:
        # Get question from request
        data = request.json
        question = data.get('question', '').strip()
        
        # Validate input
        if not question:
            return jsonify({
                'answer': 'Please ask a question!',
                'time': datetime.now().strftime('%H:%M')
            })
        
        # Log the question
        print(f"\n{'='*60}")
        print(f"📝 RECEIVED QUESTION: {question}")
        print(f"⏰ Time: {datetime.now().strftime('%H:%M:%S')}")
        print(f"{'='*60}")
        
        # Route the question and get answer
        answer = route_question(question)
        
        # Return answer with timestamp
        return jsonify({
            'answer': answer,
            'time': datetime.now().strftime('%H:%M')
        })
        
    except Exception as e:
        print(f"❌ ERROR in /ask: {str(e)}")
        return jsonify({
            'answer': f'Sorry, an error occurred: {str(e)}',
            'time': datetime.now().strftime('%H:%M')
        }), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'running',
        'knowledge_base': 'configured' if os.getenv('KNOWLEDGE_BASE_ID') else 'not configured',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/debug', methods=['GET'])
def debug():
    """Debug endpoint to test knowledge base"""
    result = test_knowledge_base()
    return jsonify({'debug': 'Check console for results'})

@app.route('/test-sales', methods=['POST'])
def test_sales():
    """Test endpoint specifically for sales queries"""
    try:
        data = request.json
        question = data.get('question', 'total sales in california')
        
        from bedrock_client import ask_company_data
        answer = ask_company_data(question)
        
        return jsonify({
            'question': question,
            'answer': answer,
            'time': datetime.now().strftime('%H:%M')
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 STARTING AI AGENT - STUDENT PROJECT")
    print("="*60)
    print("📚 Second Year Data Engineering")
    print("🔧 Amazon Bedrock + Knowledge Base")
    print("💡 Enhanced prompts for better results")
    print("="*60)
    print("🌐 Web interface: http://localhost:5000")
    print("🩺 Health check: http://localhost:5000/health")
    print("🔧 Debug: http://localhost:5000/debug")
    print("⌨️  Press Ctrl+C to stop")
    print("="*60 + "\n")
    
    app.run(debug=True, port=5000, host='0.0.0.0')