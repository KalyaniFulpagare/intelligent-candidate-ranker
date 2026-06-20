import json, argparse, os
from datetime import datetime
from src.honeypot import detect_honeypot

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidates", required=True)
    parser.add_argument("--out", default="./data/")
    args = parser.parse_args()
    os.makedirs(args.out, exist_ok=True)
    out_path = os.path.join(args.out, "honeypot_ids.json")
    print(f"Scanning: {args.candidates}")
    honeypot_ids, details, total = [], [], 0
    with open(args.candidates) as f:
        for i, line in enumerate(f):
            line = line.strip()
            if not line: continue
            c = json.loads(line)
            total += 1
            is_hp, reasons = detect_honeypot(c)
            if is_hp:
                honeypot_ids.append(c["candidate_id"])
                details.append({
                    "candidate_id": c["candidate_id"],
                    "title": c["profile"]["current_title"],
                    "yoe": c["profile"]["years_of_experience"],
                    "reasons": reasons
                })
            if (i+1) % 10000 == 0:
                print(f"  ...{i+1} scanned, {len(honeypot_ids)} honeypots")
    result = {
        "honeypot_ids": honeypot_ids,
        "count": len(honeypot_ids),
        "total_scanned": total,
        "generated_at": datetime.now().isoformat(),
        "details": details
    }
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2)
    print(f"Done. {len(honeypot_ids)} honeypots found. Saved to {out_path}")

if __name__ == "__main__":
    main()
