from insight.models import Interaction


def test_ids_are_stable():
  rec = Interaction.from_turns("c1", [("customer", "Hi"), ("agent", "Hello")])
  assert [l.line_id for l in rec.lines] == ["L0001", "L0002"]


def test_round_trip():
  rec = Interaction.from_turns("c1", [("customer", "Hi")])
  assert Interaction.model_validate_json(rec.model_dump_json()) == rec
