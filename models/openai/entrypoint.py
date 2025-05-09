from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import openai
from pydantic import BaseModel
import os
import io

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TTSRequest(BaseModel):
    message: str

@app.post("/")
def respond(request: TTSRequest):
    response = openai.chat.completions.create(
        model="gpt-4.1-nano",
        messages=[{"role": "system", "content": "Du bist ein ai Model und Abbild eines Uni Dozenten. Antworte auf Fragen immer präzise und genau"}, {"role": "user", "content": request.message}]
    )
    return response.choices[0].message.content