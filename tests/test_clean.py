"""clean.py: every rejection rule, duplicates, and the count identity."""
import clean

GOOD = '{"intent": "weather_query", "date": null, "time": null, "place": "london"}'
T = "what is the weather in london"


def test_each_rule():
    assert clean.check(T, "not json")[0] == "invalid_json"
    assert clean.check(T, '{"intent": "weather_query", "date": null, "time": null}')[0] == "wrong_keys"
    assert clean.check(T, '{"intent": "play", "date": null, "time": null, "place": null}')[0] == "bad_intent"
    assert clean.check(T, '{"intent": "weather_query", "date": null, "time": null, "place": "paris"}')[0] == "invented_slot"
    assert clean.check(T, GOOD)[0] is None


def test_duplicates_keep_smallest_id_and_counts_add_up():
    recs = [{"id": "C0003", "text": T, "teacher_raw": GOOD},
            {"id": "C0001", "text": T, "teacher_raw": GOOD},
            {"id": "C0002", "text": T, "teacher_raw": "oops"}]
    kept, c = clean.clean(recs)
    assert [r["id"] for r in kept] == ["C0001"]
    assert c["input"] == c["invalid_json"] + c["wrong_keys"] + c["bad_intent"] + c["invented_slot"] + c["duplicate"] + c["kept"]
