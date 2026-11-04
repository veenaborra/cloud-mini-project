"""Teacher on validation.jsonl with the SAME prompt and settings as labelling."""
import json, urllib.request
tpl = open("prompts/teacher_prompt.txt").read()
rows = [json.loads(l) for l in open("data/validation.jsonl") if l.strip()]
with open("results/teacher_predictions.jsonl", "w") as f:
    for i, r in enumerate(rows, 1):
        body = {"model": "phi3.5", "prompt": tpl.replace("{command}", r["text"]), "stream": False,
                "format": "json", "options": {"temperature": 0, "seed": 42}}
        req = urllib.request.Request("http://host.docker.internal:11434/api/generate",
                                     json.dumps(body).encode(), {"Content-Type": "application/json"})
        raw = json.loads(urllib.request.urlopen(req, timeout=300).read())["response"]
        f.write(json.dumps({"id": r["id"], "prediction": raw}) + "\n")
        if i % 10 == 0: print(i, "/", len(rows), flush=True)
