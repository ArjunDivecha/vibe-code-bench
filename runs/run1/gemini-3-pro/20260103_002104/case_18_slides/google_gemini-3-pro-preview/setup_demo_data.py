import os

slides = {
    "slide1.txt": """Q3 Financial Overview
Revenue grew by 15% quarter-over-quarter.
Operating margins improved due to cost-cutting measures.
We exceeded our EBITDA targets by 5%.
Key drivers: Cloud services and Enterprise licensing.""",

    "slide2.txt": """Product Roadmap Update
Launch of 'Phoenix' module scheduled for October.
Beta testing showed 98% user satisfaction.
Mobile app refactor is 60% complete.
Deferred: Legacy API deprecation pushed to Q1 next year.""",

    "slide3.txt": """Marketing Strategy 2024
Focus on inbound lead generation via content marketing.
Budget allocation: 40% Digital, 30% Events, 30% Partnerships.
New influencer campaign launching in Europe.
Targeting a 20% increase in MQLs.""",

    "slide4.txt": """Team & HR
Headcount increased by 12 employees this quarter.
Employee retention rate stands at 94%.
New wellness benefits package rolled out.
Open roles: Senior DevOps, Product Manager, Sales VP.""",

    "slide5.txt": """Risks & Mitigations
Supply chain volatility remains a concern for hardware division.
Mitigation: Diversifying supplier base in SEA region.
Cybersecurity audit highlighted minor vulnerabilities.
Action: Patching schedule accelerated to weekly cycles."""
}

def create_slides():
    print("Creating sample slide files...")
    for filename, content in slides.items():
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)
        print(f" - Created {filename}")
    print("Done. You can now run 'python generate_report.py'")

if __name__ == "__main__":
    create_slides()