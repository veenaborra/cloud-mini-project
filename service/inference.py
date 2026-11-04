"""Prompt format + generation, shared by training, evaluation and the service."""
import torch

PROMPT = "Command: {text}\nJSON:"


def format_prompt(text):
    return PROMPT.format(text=text.strip())


def load(model_dir, threads=None):
    from transformers import AutoModelForCausalLM, AutoTokenizer
    if threads:
        torch.set_num_threads(int(threads))
    tok = AutoTokenizer.from_pretrained(model_dir)
    model = AutoModelForCausalLM.from_pretrained(model_dir)
    model.eval()
    return tok, model


@torch.inference_mode()
def generate(tok, model, text, max_new_tokens=48):
    enc = tok(format_prompt(text), return_tensors="pt")
    out = model.generate(input_ids=enc["input_ids"], attention_mask=enc["attention_mask"],
                         max_new_tokens=int(max_new_tokens), do_sample=False,
                         eos_token_id=tok.eos_token_id, pad_token_id=tok.eos_token_id)
    text_out = tok.decode(out[0, enc["input_ids"].shape[1]:], skip_special_tokens=True)
    return text_out.strip().split("\n", 1)[0].strip()   # one line of JSON
