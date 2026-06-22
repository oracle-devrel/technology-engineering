# token_server.py
import os
from fastapi import FastAPI
from pydantic import BaseModel
from livekit import api
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
load_dotenv()
from pathlib import Path

load_dotenv(Path(__file__).resolve().parent / ".env")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # for now, allow everything
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TokenRequest(BaseModel):
    room_name: str
    participant_identity: str = "web-user"
    participant_name: str = "Web User"

@app.post("/api/token")
async def get_token(body: TokenRequest):
    at = (
        api.AccessToken(
            os.environ["LIVEKIT_API_KEY"],
            os.environ["LIVEKIT_API_SECRET"],
        )
        .with_identity(body.participant_identity)
        .with_name(body.participant_name)
        .with_grants(
            api.VideoGrants(
                room_join=True,
                room=body.room_name,
                can_publish=True,
                can_subscribe=True,
            )
        )
    )
    return {
        "server_url": os.environ["LIVEKIT_URL"],
        "participant_token": at.to_jwt(),
    }