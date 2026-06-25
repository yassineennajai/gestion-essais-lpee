import requests
import time
import json
from config import MANUS_API_KEY, MANUS_API_URL

class ManusClient:
    def __init__(self, api_key=MANUS_API_KEY, base_url=MANUS_API_URL):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def create_task(self, prompt, task_mode="agent", agent_profile="manus-1.5"):
        """
        Create a new task for Manus AI agent.
        
        Args:
            prompt: The task description
            task_mode: 'agent' for autonomous mode or 'chat' for interactive
            agent_profile: Which Manus agent version to use
        
        Returns:
            Task ID if successful, None otherwise
        """
        url = f"{self.base_url}/tasks"
        
        payload = {
            "agentProfile": agent_profile,
            "taskMode": task_mode,
            "task": prompt
        }
        
        try:
            print(f"🤖 Creating Manus AI task for: {prompt[:50]}...")
            
            response = requests.post(
                url, 
                headers=self.headers, 
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            
            task_data = response.json()
            task_id = task_data.get('task_id')
            
            if task_id:
                print(f"✅ Manus task created successfully. Task ID: {task_id}")
                return task_id
            else:
                print("⚠️ Task created but no task ID returned")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Error creating Manus task: {str(e)}")
            return None
    
    def get_task_status(self, task_id):
        """
        Get the status and result of a Manus task.
        
        Args:
            task_id: The ID of the task to check
        
        Returns:
            Tuple of (status, output)
        """
        url = f"{self.base_url}/tasks/{task_id}"
        
        try:
            response = requests.get(
                url, 
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            
            task_info = response.json()
            status = task_info.get('status', 'unknown')
            output = task_info.get('output')
            
            # Additional metadata
            metadata = {
                'created_at': task_info.get('created_at'),
                'completed_at': task_info.get('completed_at'),
                'execution_time': task_info.get('execution_time')
            }
            
            return status, output, metadata
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Error getting Manus task status: {str(e)}")
            return 'error', None, {}
    
    def wait_for_completion(self, task_id, poll_interval=5, timeout=300):
        """
        Poll for task completion until timeout.
        
        Args:
            task_id: Task ID to monitor
            poll_interval: Seconds between status checks
            timeout: Maximum seconds to wait
        
        Returns:
            Final output or None if timeout
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            status, output, _ = self.get_task_status(task_id)
            
            if status == 'completed':
                print(f"✅ Task {task_id} completed successfully")
                return output
            elif status == 'failed':
                print(f"❌ Task {task_id} failed")
                return None
            elif status == 'running':
                elapsed = int(time.time() - start_time)
                print(f"⏳ Task {task_id} still running... ({elapsed}s elapsed)")
            
            time.sleep(poll_interval)
        
        print(f"⏰ Timeout waiting for task {task_id}")
        return None
    
    def upload_attachment(self, file_path):
        """
        Upload a file to be used with a Manus task.
        
        Args:
            file_path: Path to the file to upload
        
        Returns:
            File ID or None
        """
        url = f"{self.base_url}/files"
        
        try:
            with open(file_path, 'rb') as f:
                files = {'file': f}
                response = requests.post(
                    url,
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    files=files,
                    timeout=60
                )
                response.raise_for_status()
                
                file_data = response.json()
                file_id = file_data.get('file_id')
                print(f"✅ File uploaded successfully. File ID: {file_id}")
                return file_id
                
        except Exception as e:
            print(f"❌ Error uploading file: {str(e)}")
            return None
         
   
