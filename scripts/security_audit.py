import os
import re

# Regex for common secret patterns
patterns = [
    (re.compile(r'(api[_-]?key|secret|password|passwd|token)\s*[:=]\s*["\']([^"\']{8,})["\']', re.I), "Secret Assignment"),
    (re.compile(r'ghp_[a-zA-Z0-9]{36}|gho_[a-zA-Z0-9]{36}'), "GitHub Token"),
    (re.compile(r'[0-9]{8,10}:[a-zA-Z0-9_-]{35}'), "Telegram Bot Token"),
    (re.compile(r'AIza[0-9A-Za-z-_]{35}'), "Google API Key"),
    (re.compile(r'ey[A-Za-z0-9-_=]+\.[A-Za-z0-9-_=]+\.?[A-Za-z0-9-_.+/=]*'), "JWT Token"),
]

def scan_file(fpath):
    issues = []
    try:
        with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
            for idx, line in enumerate(f, 1):
                for pat, label in patterns:
                    m = pat.search(line)
                    if m:
                        # exclude placeholder strings
                        val = m.group(0)
                        if "example" in val.lower() or "placeholder" in val.lower() or "yourexness" in val.lower():
                            continue
                        issues.append((idx, label, val[:40]))
    except Exception as e:
        pass
    return issues

def main():
    print("=== SECURITY & SENSITIVE DATA SCAN ===")
    exclude_dirs = {".git", "__pycache__", "data", ".gemini", "node_modules", "venv", ".venv"}
    found_any = False
    
    for root, dirs, files in os.walk("."):
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        for f in files:
            if f == ".env" or f.endswith(".pyc"):
                continue
            fpath = os.path.join(root, f)
            issues = scan_file(fpath)
            if issues:
                found_any = True
                print(f"\n[!] {fpath}:")
                for line_no, label, preview in issues:
                    print(f"    Line {line_no} [{label}]: {preview}")
                    
    if not found_any:
        print("\n[OK] No hardcoded secrets or credentials detected outside of .env!")

if __name__ == "__main__":
    main()
