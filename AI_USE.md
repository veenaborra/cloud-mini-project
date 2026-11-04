# AI use

## Tools used
- **Claude (Anthropic)**, used as a step-by-step tutor and pair programmer throughout the project.
- No other AI tools. No AI was used to generate labels, scores or measurements.

## What I used it for
| Area | How AI helped | What I did myself |
|---|---|---|
| Environment setup | Commands for WSL2, Docker Desktop, k3d, kubectl, Ollama | Diagnosed and fixed real setup problems: a full Ubuntu partition (moved to WSL), Ollama listening only on 127.0.0.1, a firewall rule, a stale `host.docker.internal` entry in the Windows hosts file, and a Windows clock 5.5 h off that broke Pod ages and timings |
| Task 1: storage and labelling | Drafts of the k3d config, SeaweedFS manifest, worker, Indexed Job and clean.py | Wrote and tuned the teacher prompt over several iterations (fixed `07:00`-style conversions and reminders labelled as alarms); tested it on 20 commands before the full run; ran 2 workers for ~6 h; handled transient DNS failures; inspected 187 rejected records and grouped them into patterns (paraphrasing, spelling fixes, invented values, few-shot leakage) |
| Task 2: training | Draft training loop with prompt masking, config, packaging script | Ran SUBSET=50, v1 and v2; interpreted the loss curves; found that v2 had lower training loss but no better validation score (overfitting); verified that the Release checksum, the local file and object storage all match |
| Task 3: service | Draft FastAPI app, pinned requirements, Dockerfile | Built and tested the image under 1 CPU / 1 GiB; checked 503 while loading, 200 when ready, 500 with FAULT_INJECT; fixed a missing home directory for the container user; explained why peak memory (620 MiB) exceeds steady state (343 MiB) |
| Task 4: Kubernetes | Draft Deployment, Service, Ingress, HPA and experiment commands | Ran every experiment and read the evidence; diagnosed a failed recovery test (deleting the only ready Pod gave Traefik 404s, amplified by fast failures) and re-ran it correctly with 2 ready replicas |
| Task 5: networking | Explanation of NACL evaluation and subnet method | Worked out the subnet table by hand, then verified it with Python `ipaddress` and the NACL with `nacl_sim.py` (6/6) |
| Task 6: CI/CD | Draft workflow, unit tests, Makefile targets | Fixed lint findings; ran the pipeline green and once with the untrained model to show the gate failing; tested `make up` from a fresh clone |

## How I checked the AI's output
1. **Ran everything myself.** Every number in the report comes from files in `results/`, produced on my laptop.
2. **Compared against the handout.** Each step was checked against the marking table before moving on.
3. **Independent checks:** unit tests (7) and ruff in CI; `score.py`, `nacl_sim.py` and `sha256sum` for results; Python `ipaddress` for subnets.
4. **Did not accept wrong output.** Examples:
   - A cold-start summary line wrongly included download timings; I removed it and recomputed the median from the Pod timestamps.
   - The first recovery test failed (76% errors); instead of hiding it, I found the cause and kept both runs as evidence.
   - The worker's progress estimate was wrong because of the clock problem; I tracked real progress by record counts.

## What I learnt
- Sequence-level knowledge distillation in practice: a 70M student reached 41% full-frame accuracy against the teacher's 49%, and inherited the teacher's mistakes.
- How readiness and liveness probes, rolling updates (`maxUnavailable: 0`), preStop hooks and the HPA interact to keep a service available.
- That redundancy needs at least two ready replicas, which I saw directly when a single-replica test failed.
- Practical debugging across layers: Windows, WSL, Docker, Kubernetes DNS, object storage and the network.
