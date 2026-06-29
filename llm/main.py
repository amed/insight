# P3 module
import os
from fastapi import FastAPI
from pydantic import BaseModel
from openai import OpenAI

app = FastAPI()
client = OpenAI(base_url=os.environ["LLM_BASE_URL"], api_key=os.environ["LLM_API_KEY"])

MODEL = os.environ["LLM_MODEL"]

PROMPT = "Extract the customer's intent from this conversation. Reply with one short phrase.\n\n{text}"


class Request(BaseModel):
  text: str


@app.post("/extract")
def extract(req: Request):
  response = client.chat.completions.create(
    model=MODEL,
    messages=[{"role": "user", "content": PROMPT.format(text=req.text)}],
  )
  return {"intent": response.choices[0].message.content.strip()}