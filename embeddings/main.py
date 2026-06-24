from fastapi import FastAPI
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer

app = FastAPI()
model = SentenceTransformer("all-MiniLM-L6-v2")


class Request(BaseModel):
  texts: list[str]


@app.post("/embed")
def embed(req: Request):
  return {"vectors": model.encode(req.texts).tolist()}