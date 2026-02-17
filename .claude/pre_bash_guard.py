import sys

dangerous = ["rm -rf", "sudo", "mv * /"]

cmd = sys.stdin.read()

for d in dangerous:
    if d in cmd:
        print("BLOCKED: Dangerous command detected.")
        sys.exit(1)

sys.exit(0)