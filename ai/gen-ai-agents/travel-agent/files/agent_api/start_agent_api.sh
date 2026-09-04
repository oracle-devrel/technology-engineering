# start the Agent API
export PYTHONPATH="..:$PYTHONPATH"
uvicorn agent_fastapi:app --port 8080 --reload
