import requests
import json

def seed_chromadb():
    url = "http://localhost:8000/classify/seed"
    headers = {"Content-Type": "application/json"}
    
    seeds = [
        # Math prompts
        {"text": "Solve the system of equations: 3x + 2y = 12 and x - y = 4", "category": "math"},
        {"text": "Find the derivative of f(x) = x^3 * ln(x) with respect to x", "category": "math"},
        {"text": "What is the area under the curve y = sin(x) from 0 to pi?", "category": "math"},
        {"text": "Prove that the square root of 2 is irrational", "category": "math"},
        {"text": "Calculate the probability of drawing three aces in a row from a deck of cards", "category": "math"},
        {"text": "Determine the eigenvalues and eigenvectors of the matrix [[1, 2], [2, 1]]", "category": "math"},
        {"text": "Find the limit as x approaches infinity of (3x^2 + 5x) / (2x^2 - 1)", "category": "math"},
        {"text": "What is the Fourier transform of a rectangular pulse?", "category": "math"},
        
        # Coding prompts
        {"text": "Write a python function to check if a binary tree is balanced", "category": "coding"},
        {"text": "Implement the quicksort algorithm in C++ with pivot selection", "category": "coding"},
        {"text": "How do I make a POST request with headers in JavaScript using fetch?", "category": "coding"},
        {"text": "Write a regex pattern to validate email addresses according to standards", "category": "coding"},
        {"text": "Explain the difference between interface and abstract class in Java", "category": "coding"},
        {"text": "Create an HTML form with CSS styling for a dark-mode login page", "category": "coding"},
        {"text": "How do I perform a database migration using alembic in SQLAlchemy?", "category": "coding"},
        {"text": "Write a shell script to compress all log files modified in the last 7 days", "category": "coding"},
        
        # Research prompts
        {"text": "Explain the historical significance of the Magna Carta in modern democracy", "category": "research"},
        {"text": "Provide an overview of the causes and major events of the French Revolution", "category": "research"},
        {"text": "Compare and contrast key features of Keynesianism vs Monetarism economics", "category": "research"},
        {"text": "Summarize the scientific consensus on the effects of microplastics in oceans", "category": "research"},
        {"text": "What is the background of the space race between USA and USSR?", "category": "research"},
        {"text": "Explain the concept of quantum superposition using Schrödinger's cat thought experiment", "category": "research"},
        {"text": "Describe the architectural styles of gothic cathedrals in medieval Europe", "category": "research"},
        {"text": "Who is Alan Turing and what was his contribution to computer science?", "category": "research"},
        
        # Casual prompts
        {"text": "Hello! How is your day going?", "category": "casual_chat"},
        {"text": "Tell me a joke about programming or debugging", "category": "casual_chat"},
        {"text": "What are some good hobbies to pick up during winter?", "category": "casual_chat"},
        {"text": "What is your favorite book recommendation?", "category": "casual_chat"},
        {"text": "Give me a motivational quote to start the morning", "category": "casual_chat"},
        {"text": "How do you make a perfect cup of espresso?", "category": "casual_chat"}
    ]
    
    payload = {"seeds": seeds}
    
    print(f"Sending {len(seeds)} seed prompts to {url}...")
    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        if response.status_code == 200:
            print("✓ ChromaDB seeding successful!")
            print(response.json())
        else:
            print(f"✗ Seeding failed with status code {response.status_code}: {response.text}")
    except Exception as e:
        print(f"✗ Connection error during seeding: {e}")

if __name__ == "__main__":
    seed_chromadb()
