from pydantic import BaseModel


class Line(BaseModel):
  line_id: str      # stable, e.g. "L0001"
  speaker: str      # "customer" or "agent"
  text: str


class Interaction(BaseModel):
  interaction_id: str
  lines: list[Line]

  @classmethod
  def from_turns(cls, interaction_id: str, turns: list[tuple[str, str]]) -> "Interaction":
    lines = [
      Line(line_id=f"L{i:04d}", speaker=speaker, text=text)
      for i, (speaker, text) in enumerate(turns, start=1)
    ]

    return cls(interaction_id=interaction_id, lines=lines)