from fastapi import FastAPI
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer, util

app = FastAPI()
model = SentenceTransformer("all-MiniLM-L6-v2")


class Request(BaseModel):
  texts: list[str]


@app.post("/embed")
def embed(req: Request):
  return {"vectors": model.encode(req.texts).tolist()}


class SearchRequest(BaseModel):
  query: str
  lines: list[str]
  top_k: int = 5


# Rank the lines against the query, return the best matches by cosine similarity.
@app.post("/search")
def search(req: SearchRequest):
  query_vec = model.encode(req.query, convert_to_tensor=True)
  line_vecs = model.encode(req.lines, convert_to_tensor=True)
  scores = util.cos_sim(query_vec, line_vecs)[0]
  k = min(req.top_k, len(req.lines))
  top = scores.topk(k)
  matches = [
    {"index": int(idx), "score": float(score)}
    for score, idx in zip(top.values, top.indices)
  ]
  return {"matches": matches}
