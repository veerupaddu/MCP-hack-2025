# Custom Training Data
# Add high-quality, manually created QA pairs

import json

custom_qa_pairs = [
    {
        "instruction": "Which prefecture has the largest population in Japan?",
        "input": "Context: Japan Census data.",
        "output": "According to the 2020 Population Census, Tokyo has the largest population with 14,047,594 residents."
    },
    {
        "instruction": "What is the population density of Tokyo?",
        "input": "Context: Japan Census data.",
        "output": "Tokyo has a population density of approximately 6,402 people per square kilometer, calculated from its population of 14,047,594 and area of 2,194 km²."
    },
    {
        "instruction": "Compare the population of Tokyo and Osaka.",
        "input": "Context: Japan Census data.",
        "output": "Tokyo has a population of 14,047,594 while Osaka has 8,837,685. Tokyo's population is approximately 5.2 million larger than Osaka's."
    },
    {
        "instruction": "What percentage of Japan's population lives in Tokyo?",
        "input": "Context: Japan Census data.",
        "output": "Tokyo accounts for approximately 11.1% of Japan's total population of 126.1 million people."
    },
    # Add more custom pairs here
]

# Save to JSONL
with open('custom_train.jsonl', 'w', encoding='utf-8') as f:
    for pair in custom_qa_pairs:
        json.dump(pair, f, ensure_ascii=False)
        f.write('\n')

print(f"Created {len(custom_qa_pairs)} custom QA pairs")
