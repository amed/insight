import os
from fastapi import FastAPI
from pydantic import BaseModel
from openai import OpenAI

app = FastAPI()
client = OpenAI(
  base_url=os.environ["LLM_BASE_URL"],
  api_key=os.environ["LLM_API_KEY"],
)
MODEL = os.environ["LLM_MODEL"]


class Request(BaseModel):
  text: str


@app.post("/extract")
def extract(req: Request):
  response = client.chat.completions.create(
      model=MODEL,
      messages=[{"role": "user", "content": req.text}],
  )
  return {"reply": response.choices[0].message.content}