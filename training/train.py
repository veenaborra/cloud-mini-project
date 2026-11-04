"""Fine-tune Pythia-70M on the teacher's replies (sequence-level KD).

  python training/train.py --version v1 [--subset 50]
All hyper-parameters come from training/config.yaml.
"""
import argparse, csv, json, math, os, random, sys, time

import numpy as np
import torch
import yaml

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.join(ROOT, "service"))
from inference import format_prompt  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", default="v1")
    ap.add_argument("--subset", type=int, default=0)
    a = ap.parse_args()
    from transformers import AutoModelForCausalLM, AutoTokenizer, get_linear_schedule_with_warmup

    cfg = yaml.safe_load(open(os.path.join(ROOT, "training", "config.yaml")))
    cfg.update(cfg["versions"].get(a.version) or {})

    # fixed seed everywhere -> same result every run
    seed = int(cfg["seed"])
    random.seed(seed); np.random.seed(seed); torch.manual_seed(seed)

    limit = min(a.subset, cfg["max_records"]) if a.subset else cfg["max_records"]
    rows = [json.loads(l) for l in open(os.path.join(ROOT, cfg["train_file"]), encoding="utf-8") if l.strip()][:limit]
    tag = a.version + (f"-subset{a.subset}" if a.subset else "")
    out_dir = os.path.join(ROOT, "build", f"model-{tag}")
    loss_path = os.path.join(ROOT, "training", "loss.csv" if a.version == "v1" else f"loss_{a.version}.csv")
    print(f"{tag}: {len(rows)} records, {cfg['num_epochs']} epochs, lr {cfg['learning_rate']}, bs {cfg['batch_size']}")

    tok = AutoTokenizer.from_pretrained(cfg["base_model"])
    model = AutoModelForCausalLM.from_pretrained(cfg["base_model"])
    model.train()

    # build (input_ids, labels); labels = -100 on the prompt so only the JSON is learned
    data = []
    for r in rows:
        p = tok(format_prompt(r["text"]))["input_ids"]
        full = tok(format_prompt(r["text"]) + " " + r["target"])["input_ids"] + [tok.eos_token_id]
        full = full[:cfg["max_seq_length"]]
        data.append((full, ([-100] * len(p) + full[len(p):])[:len(full)]))

    bs, epochs = int(cfg["batch_size"]), int(cfg["num_epochs"])
    total = math.ceil(len(data) / bs) * epochs
    opt = torch.optim.AdamW(model.parameters(), lr=float(cfg["learning_rate"]))
    sched = get_linear_schedule_with_warmup(opt, int(cfg["warmup_ratio"] * total), total)
    rng = random.Random(seed)
    losses, t0 = [], time.time()

    for epoch in range(1, epochs + 1):
        idx = list(range(len(data))); rng.shuffle(idx)
        tot, ntok = 0.0, 0
        for s in range(0, len(idx), bs):
            batch = [data[i] for i in idx[s:s + bs]]
            n = max(len(x) for x, _ in batch)
            ids = torch.full((len(batch), n), tok.eos_token_id)       # pad
            lab = torch.full((len(batch), n), -100)
            att = torch.zeros((len(batch), n), dtype=torch.long)
            for i, (x, y) in enumerate(batch):
                ids[i, :len(x)] = torch.tensor(x); lab[i, :len(y)] = torch.tensor(y); att[i, :len(x)] = 1
            out = model(input_ids=ids, attention_mask=att, labels=lab)
            out.loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step(); sched.step(); opt.zero_grad()
            k = int((lab[:, 1:] != -100).sum())
            tot += out.loss.item() * k; ntok += k
        losses.append((epoch, round(tot / ntok, 6)))
        print(f"epoch {epoch}: loss {tot / ntok:.4f}  ({time.time() - t0:.0f}s)", flush=True)

    with open(loss_path, "w", newline="") as f:
        w = csv.writer(f); w.writerow(["epoch", "train_loss"]); w.writerows(losses)
    os.makedirs(out_dir, exist_ok=True)
    model.save_pretrained(out_dir); tok.save_pretrained(out_dir)
    json.dump({"model_version": a.version, "records": len(rows), **{k: cfg[k] for k in
              ("base_model", "seed", "learning_rate", "batch_size", "num_epochs", "max_seq_length")}},
              open(os.path.join(out_dir, "version.json"), "w"), indent=2, sort_keys=True)
    print(f"saved {out_dir}, loss -> {loss_path}, {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
