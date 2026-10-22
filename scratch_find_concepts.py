with open('app/core/socratic_engine.py', encoding='utf-8') as f:
    for i, line in enumerate(f):
        if line.startswith('    "') and '": {' in line:
            print(f"{i+1}: {line.strip()}")
