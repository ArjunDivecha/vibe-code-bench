import os

def create_slides():
    if not os.path.exists('slides'):
        os.makedirs('slides')

    slides_data = [
        ("slide1.txt", "Q1 Financial Overview\n\n- Revenue increased by 15% YoY.\n- Operating costs reduced by 5%.\n- Strong performance in the APAC region.\n- Key driver: New product launch in February."),
        ("slide2.txt", "Product Roadmap 2024\n\n- Q2: Launch of Mobile App v2.0.\n- Q3: Integration with major CRM platforms.\n- Q4: AI-driven analytics dashboard.\n- Focus on user retention and engagement features."),
        ("slide3.txt", "Team Expansion Plan\n\n- Hiring 5 new backend engineers.\n- Establishing a dedicated QA team.\n- Expanding the sales team in Europe.\n- Budget allocation approved for recruitment agencies."),
        ("slide10.txt", "Risk Assessment\n\n- Market volatility remains a concern.\n- Cybersecurity threats increasing in the sector.\n- Supply chain disruptions affecting hardware delivery.\n- Mitigation strategy: Diversifying suppliers and enhancing security protocols."),
        ("slide4.txt", "Marketing Strategy\n\n- Shift focus to digital channels.\n- Increase budget for social media ads.\n- Partnership with key industry influencers.\n- Goal: 20% increase in inbound leads.")
    ]

    for filename, content in slides_data:
        with open(os.path.join('slides', filename), 'w', encoding='utf-8') as f:
            f.write(content)
    
    print(f"Created {len(slides_data)} sample slides in 'slides/' directory.")

if __name__ == "__main__":
    create_slides()