"""CLI for scoremap."""
import sys, json, argparse
from .core import Scoremap

def main():
    parser = argparse.ArgumentParser(description="ScoreMap — AI Test Prep Coach. Personalized SAT/GRE/GMAT preparation with adaptive practice.")
    parser.add_argument("command", nargs="?", default="status", choices=["status", "run", "info"])
    parser.add_argument("--input", "-i", default="")
    args = parser.parse_args()
    instance = Scoremap()
    if args.command == "status":
        print(json.dumps(instance.get_stats(), indent=2))
    elif args.command == "run":
        print(json.dumps(instance.process(input=args.input or "test"), indent=2, default=str))
    elif args.command == "info":
        print(f"scoremap v0.1.0 — ScoreMap — AI Test Prep Coach. Personalized SAT/GRE/GMAT preparation with adaptive practice.")

if __name__ == "__main__":
    main()
