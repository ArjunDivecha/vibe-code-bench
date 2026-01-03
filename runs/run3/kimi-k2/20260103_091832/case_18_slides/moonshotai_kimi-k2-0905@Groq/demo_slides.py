#!/usr/bin/env python3
"""
Demo script to create sample slide files for testing the Slide Summary Reporter
"""

def create_demo_slides():
    """Create sample slide text files for demonstration"""
    
    slides = [
        {
            'filename': 'slide1.txt',
            'content': """# Introduction to Machine Learning

Welcome to the future of technology
Understanding AI and its applications
What you'll learn in this presentation"""
        },
        {
            'filename': 'slide2.txt',
            'content': """# What is Machine Learning?

A subset of artificial intelligence
Systems that learn from data
- Pattern recognition
- Decision making
- Continuous improvement"""
        },
        {
            'filename': 'slide3.txt',
            'content': """# Types of Machine Learning

1. Supervised Learning
2. Unsupervised Learning  
3. Reinforcement Learning

Each type serves different purposes"""
        },
        {
            'filename': 'slide4.txt',
            'content': """# Supervised Learning

Learning from labeled examples
- Classification tasks
- Regression problems
Common algorithms:
* Decision Trees
* Neural Networks
* Support Vector Machines"""
        },
        {
            'filename': 'slide5.txt',
            'content': """# Real-World Applications

* Healthcare: Disease diagnosis
* Finance: Fraud detection
* Retail: Recommendation systems
* Automotive: Self-driving cars
* Entertainment: Content personalization"""
        },
        {
            'filename': 'slide6.txt',
            'content': """# Challenges in ML

Data quality issues
- Missing values
- Outliers
- Imbalanced datasets

Ethical considerations
- Bias in algorithms
- Privacy concerns
- Transparency"""
        },
        {
            'filename': 'slide7.txt',
            'content': """# Future Trends

Explainable AI (XAI)
Federated Learning
Quantum Machine Learning
Edge Computing Integration

The future is bright and exciting!"""
        }
    ]
    
    for slide in slides:
        with open(slide['filename'], 'w', encoding='utf-8') as f:
            f.write(slide['content'])
        print(f"Created: {slide['filename']}")
    
    print(f"\n✅ Created {len(slides)} demo slide files!")
    print("Now run: python slide_reporter.py")


if __name__ == "__main__":
    create_demo_slides()