with open('app/core/tutoring_engine.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if line.strip().startswith('#') and any(k in line for k in ['Round Robin:', 'FCFS:', 'SJF:', 'SRTF:', 'Priority:', 'HRRN:', 'MLFQ:', 'CFS:', 'Real-Time', 'Multiprocessor:', 'Stride']):
        print(f"Line {i+1}: {line.strip()}")
