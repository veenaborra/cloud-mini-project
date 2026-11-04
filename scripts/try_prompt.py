import json, sys, time, urllib.request
tpl = open("prompts/teacher_prompt.txt").read()
cmds = [json.loads(line)["text"] for line in open("data/commands_pool.jsonl")][:int(sys.argv[1]) if len(sys.argv) > 1 else 10]
for c in cmds:
    body = {"model": "phi3.5", "prompt": tpl.replace("{command}", c), "stream": False,
            "format": "json", "options": {"temperature": 0, "seed": 42}}
    t = time.time()
    req = urllib.request.Request("http://host.docker.internal:11434/api/generate",
                                 json.dumps(body).encode(), {"Content-Type": "application/json"})
    out = json.loads(urllib.request.urlopen(req).read())["response"]
    print(f"{time.time()-t:5.1f}s  {c}\n       {out.strip()}")
