import re

files = {
    'Bosses': r'C:\Users\march\.gemini\antigravity\brain\3eec0980-c14b-4517-b984-678dee2dd4e2\.system_generated\steps\55\content.md',
    'Resonance (Bells)': r'C:\Users\march\.gemini\antigravity\brain\3eec0980-c14b-4517-b984-678dee2dd4e2\.system_generated\steps\59\content.md',
    'Races (Aspects)': r'C:\Users\march\.gemini\antigravity\brain\3eec0980-c14b-4517-b984-678dee2dd4e2\.system_generated\steps\61\content.md',
    'Oaths': r'C:\Users\march\.gemini\antigravity\brain\3eec0980-c14b-4517-b984-678dee2dd4e2\.system_generated\steps\63\content.md',
    'Attunements': r'C:\Users\march\.gemini\antigravity\brain\3eec0980-c14b-4517-b984-678dee2dd4e2\.system_generated\steps\65\content.md'
}

for cat, fpath in files.items():
    print(f"\n==================== {cat} ====================")
    with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
        text = f.read()
    
    # Extract links with title attribute or text inside table/lists
    links = set(re.findall(r'title="([^"]+)"', text))
    # Filter out maintenance titles
    filtered = [l for l in links if not l.startswith(('Category:', 'File:', 'Template:', 'Help:', 'Special:', 'Edit section', 'Deepwoken Wiki', 'Expand', 'Collapse', 'Main Page'))]
    print(filtered[:35])
