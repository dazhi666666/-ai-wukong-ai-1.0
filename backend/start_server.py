import subprocess
import sys

# Start uvicorn
subprocess.Popen(
    [r"D:\0 - 副本\llm\llm-chat-app\backend\venv\Scripts\uvicorn.exe", 
     "app.main:app", 
     "--reload", 
     "--port", "8000", 
     "--host", "0.0.0.0"],
    cwd=r"D:\0 - 副本\llm\llm-chat-app\backend",
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
)
print("Started uvicorn")
