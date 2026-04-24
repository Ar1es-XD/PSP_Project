import random
import time
import os

CHARSET = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz1234567890 _+=~₹!@#$%^&*(){}[]|;:<>,.?/"

COLORS = {
    "green":  "\033[92m",
    "yellow": "\033[93m",
    "cyan":   "\033[96m",
    "red":    "\033[91m",
    "bold":   "\033[1m",
    "reset":  "\033[0m",
    "dim":    "\033[2m",
}

def color(text, *styles):
    return "".join(COLORS[s] for s in styles) + text + COLORS["reset"]

def clear():
    os.system("cls" if os.name == "nt" else "clear")

def render(cur, wanted, tries, start_time):
    clear()
    elapsed = time.time() - start_time
    matched = sum(c == w for c, w in zip(cur, wanted))
    progress = matched / len(wanted)
    bar_len = 40
    filled = int(bar_len * progress)
    bar = "█" * filled + "░" * (bar_len - filled)

    print(color("\n ╔══════════════════════════════════════╗", "cyan", "bold"))
    print(color(" ║        🔐  PASSWORD EVOLVER          ║", "cyan", "bold"))
    print(color(" ╚══════════════════════════════════════╝\n", "cyan", "bold"))

    display = ""
    for c, w in zip(cur, wanted):
        if c == w:
            display += color(c, "green", "bold")
        else:
            display += color(c, "red")
    print(f"  {display}\n")

    print(color(f"  [{bar}] {progress*100:.1f}%", "yellow"))
    print(color(f"\n  Attempt   : ", "dim") + color(str(tries), "bold"))
    print(color(f"  Matched   : ", "dim") + color(f"{matched}/{len(wanted)}", "bold"))
    print(color(f"  Elapsed   : ", "dim") + color(f"{elapsed:.2f}s", "bold"))
    print(color(f"  Speed     : ", "dim") + color(f"{tries/elapsed:.0f} tries/sec" if elapsed > 0 else "—", "bold"))

def evolve(wanted: str, delay: float = 0.0):
    target = list(wanted)
    cur = [random.choice(CHARSET) for _ in target]
    tries = 0
    start = time.time()

    while cur != target:
        tries += 1
        for i in range(len(target)):
            if cur[i] != target[i]:
                cur[i] = random.choice(CHARSET)
        if tries % 50 == 0 or cur == target:
            render(cur, target, tries, start)
            if delay:
                time.sleep(delay)

    elapsed = time.time() - start
    print(color("\n\n  ✅ Password evolved successfully!\n", "green", "bold"))
    print(color(f"  Target  : ", "dim") + color(wanted, "green", "bold"))
    print(color(f"  Attempts: ", "dim") + color(str(tries), "bold"))
    print(color(f"  Time    : ", "dim") + color(f"{elapsed:.2f}s", "bold"))
    print(color(f"  Speed   : ", "dim") + color(f"{tries/elapsed:.0f} tries/sec\n", "bold"))

if __name__ == "__main__":
    print(color("\n  🔐 PASSWORD EVOLVER", "cyan", "bold"))
    print(color("  Enter the target password: ", "yellow"), end="")
    target = input()
    if not target:
        print(color("  ⚠ No input provided. Exiting.", "red"))
    else:
        evolve(target, delay=0.01)
