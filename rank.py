import json, csv, argparse, os, time
from src.honeypot import detect_honeypot
from src.scoring import compute_final_score
from src.reasoning import generate_reasoning

def load_honeypot_ids(data_dir):
    path = os.path.join(data_dir, "honeypot_ids.json")
    if os.path.exists(path):
        with open(path) as f:
            return set(json.load(f)["honeypot_ids"])
    print("Warning: honeypot_ids.json not found — running detection inline")
    return set()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidates", required=True)
    parser.add_argument("--out", default="./submission.csv")
    parser.add_argument("--data-dir", default="./data/")
    parser.add_argument("--top-n", type=int, default=100)
    args = parser.parse_args()

    start = time.time()
    honeypot_ids = load_honeypot_ids(args.data_dir)
    print(f"{len(honeypot_ids)} honeypot IDs loaded")

    results = []
    with open(args.candidates) as f:
        for i, line in enumerate(f):
            line = line.strip()
            if not line: continue
            c = json.loads(line)
            if not honeypot_ids:
                is_hp, _ = detect_honeypot(c)
                if is_hp: continue
            r = compute_final_score(c, honeypot_ids)
            if r["excluded"] != "honeypot":
                results.append(r)
            if (i+1) % 20000 == 0:
                print(f"  ...{i+1} done in {time.time()-start:.1f}s")

    results.sort(key=lambda x: x["final_score"], reverse=True)
    top_n = results[:args.top_n]
    max_score = top_n[0]["final_score"] if top_n else 1.0

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["candidate_id", "rank", "score", "reasoning"])
        for rank, r in enumerate(top_n, 1):
            writer.writerow([
                r["candidate_id"],
                rank,
                round(r["final_score"] / max_score, 6),
                generate_reasoning(r)
            ])

    print(f"Done in {time.time()-start:.1f}s")
    print(f"Output: {args.out}")
    print(f"Top: {top_n[0]['candidate_id']} — {top_n[0]['components']['title']} at {top_n[0]['components']['company']}")

if __name__ == "__main__":
    main()
