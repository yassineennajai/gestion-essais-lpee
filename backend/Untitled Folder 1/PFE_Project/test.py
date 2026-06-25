from manus_client import ManusClient

client = ManusClient()
task_id = client.create_task("Say hello")

print("Task ID:", task_id)

