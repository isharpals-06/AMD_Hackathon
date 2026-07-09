import csv
import os
import random

OUTPUT_FILE = "./data/training_dataset.csv"

CATEGORIES = ["math", "coding", "research", "casual_chat"]

# Dictionaries of placeholder options to generate varied, realistic prompts
PLACEHOLDERS = {
    # Math placeholders
    "num": [str(i) for i in range(1, 200)],
    "var": ["x", "y", "z", "n", "t", "a", "b", "c", "k"],
    "math_func": [
        "sin(x)",
        "cos(x)",
        "tan(x)",
        "e^x",
        "ln(x)",
        "log(x)",
        "x^2",
        "1/x",
        "arctan(x)",
        "sinh(x)",
        "cosh(x)",
        "x^3",
        "sqrt(x)",
        "sin(2x)",
        "cos(3x)",
        "e^(-x^2)",
        "x*ln(x)",
    ],
    "poly": [
        "x^2 - 4",
        "3x^2 + 2x - 5",
        "x^3 - x",
        "2x^3 - 5x + 3",
        "x^2 - 9",
        "x^2 - 2x + 1",
        "4x^2 - 16",
        "x^3 - 8",
        "x^4 - 1",
        "5x^2 + 10x",
        "x^2 + 5x + 6",
        "2x^2 - 8x + 6",
    ],
    "limit_target": ["0", "1", "infinity", "pi", "e", "2", "-1", "pi/2"],
    "matrix_dim": ["2x2", "3x3", "4x4", "5x5", "n*n"],
    "math_concept": [
        "Pythagorean theorem",
        "Euler's identity",
        "Fundamental Theorem of Calculus",
        "Central Limit Theorem",
        "Bayes' theorem",
        "Taylor series expansion",
        "Mean Value Theorem",
        "L'Hopital's rule",
        "Quadratic formula",
        "Fermat's Last Theorem",
        "Riemann Hypothesis",
        "Goldbach's conjecture",
        "Collatz conjecture",
    ],
    "polygon": [
        "triangle",
        "square",
        "pentagon",
        "hexagon",
        "heptagon",
        "octagon",
        "nonagon",
        "decagon",
        "dodecagon",
        "parallelogram",
        "trapezoid",
        "rhombus",
    ],
    "series": [
        "1 + 1/2 + 1/4 + 1/8 + ...",
        "sum of 1/n^2 from 1 to infinity",
        "1 + 3 + 5 + 7 + ...",
        "sum of (-1)^n / n from 1 to infinity",
        "sum of 1/n from 1 to infinity",
        "1 + x + x^2 + x^3 + ...",
        "sum of x^n / n! from 0 to infinity",
        "1 - 1/3 + 1/5 - 1/7 + ...",
        "sum of n/2^n from 1 to infinity",
    ],
    "probability_event": [
        "rolling a sum of 7 with two dice",
        "drawing a red card from a standard deck",
        "flipping 3 heads in a row",
        "picking 2 blue marbles out of 10 without replacement",
        "winning a lottery with 1 in a million odds",
        "getting a royal flush in poker",
        "at least one success in 5 independent trials with p=0.3",
        "two independent events both occurring",
        "getting an even number on a 12-sided die",
    ],
    # Coding placeholders
    "lang": [
        "Python",
        "JavaScript",
        "C++",
        "Rust",
        "Go",
        "Java",
        "TypeScript",
        "Ruby",
        "PHP",
        "C#",
        "C",
        "Swift",
        "Kotlin",
        "Scala",
        "Haskell",
    ],
    "algo": [
        "sort an array using merge sort",
        "find the shortest path in a graph using Dijkstra's",
        "reverse a linked list",
        "check if a string is a palindrome",
        "calculate the fibonacci sequence recursively",
        "traverse a tree in pre-order",
        "detect a cycle in a directed graph",
        "find the longest common subsequence of two strings",
        "binary search in a sorted array",
        "generate all permutations of a string",
        "check if a number is prime",
        "merge two sorted linked lists",
        "find the intersection of two arrays",
        "implement run-length encoding compression",
        "validate a sudoku board",
    ],
    "data_struct": [
        "binary search tree",
        "hash map",
        "priority queue",
        "doubly linked list",
        "trie",
        "circular queue",
        "min-heap",
        "directed graph",
        "red-black tree",
        "stack",
        "adjacency list",
        "bloom filter",
    ],
    "error_type": [
        "NullPointerException",
        "IndexOutOfBoundsException",
        "TypeError",
        "AttributeError",
        "KeyError",
        "Segmentation Fault",
        "ZeroDivisionError",
        "SyntaxError",
        "IndentationError",
        "StackOverflowError",
    ],
    "framework": [
        "FastAPI",
        "React",
        "Express.js",
        "Django",
        "Spring Boot",
        "Next.js",
        "Gin",
        "Flask",
        "Angular",
        "Vue.js",
        "Laravel",
        "Ruby on Rails",
        "ASP.NET Core",
        "Svelte",
        "Fastify",
    ],
    "db_type": [
        "PostgreSQL",
        "MongoDB",
        "MySQL",
        "Redis",
        "SQLite",
        "Cassandra",
        "DynamoDB",
        "Neo4j",
        "Oracle",
        "MariaDB",
    ],
    "concurrency": [
        "goroutines and channels",
        "async/await tasks",
        "multiprocessing",
        "mutex locks",
        "thread pools",
        "semaphores",
        "promises and event loops",
        "actors pattern",
        "threads and locks",
        "reactive streams",
    ],
    "test_framework": [
        "pytest",
        "Jest",
        "JUnit",
        "Mocha",
        "cargo test",
        "unittest",
        "RSpec",
        "PHPUnit",
        "PyUnit",
    ],
    # Research placeholders
    "concept": [
        "capitalism",
        "socialism",
        "democracy",
        "monarchy",
        "renewable energy",
        "manual testing",
        "monolithic architecture",
        "microservices",
        "nuclear power",
        "quantum computing",
        "artificial intelligence",
        "classical physics",
        "relativity",
        "globalization",
        "isolationism",
        "centralized banking",
        "decentralized finance",
        "organic farming",
        "GMO crops",
        "analog systems",
        "digital systems",
        "supervised learning",
        "unsupervised learning",
        "Newtonian mechanics",
        "quantum mechanics",
        "rationalism",
        "empiricism",
        "behavioral psychology",
        "cognitive neuroscience",
    ],
    "history_event": [
        "the French Revolution",
        "the Industrial Revolution",
        "the American Civil War",
        "the fall of the Roman Empire",
        "the Space Race",
        "the Renaissance",
        "World War I",
        "World War II",
        "the Cold War",
        "the signing of Magna Carta",
        "the Bolshevik Revolution",
        "the Meiji Restoration",
        "the founding of the United Nations",
    ],
    "bio_term": [
        "mitosis",
        "meiosis",
        "photosynthesis",
        "cellular respiration",
        "DNA replication",
        "protein synthesis",
        "glycolysis",
        "natural selection",
        "genetic drift",
        "homeostasis",
        "transcription",
        "translation",
        "osmosis",
        "active transport",
        "enzymatic catalysis",
    ],
    "science_field": [
        "quantum computing",
        "nuclear fusion power",
        "CRISPR gene editing",
        "superconducting materials",
        "gravitational wave detection",
        "dark matter research",
        "nanotechnology in medicine",
        "climate engineering",
        "neuroprosthetics",
        "biofuels production",
        "astrophysics",
        "quantum cryptography",
    ],
    "econ_term": [
        "hyperinflation",
        "the Great Depression",
        "stagflation",
        "market monopoly",
        "supply chain disruptions",
        "fiscal policy",
        "monetary easing",
        "trade tariffs",
        "market speculation",
        "consumer price index",
    ],
    "ethical_issue": [
        "artificial intelligence bias",
        "human gene editing",
        "climate engineering",
        "data privacy laws",
        "autonomous weapons",
        "animal testing",
        "facial recognition surveillance",
        "algorithmic censorship",
    ],
    # Casual Chat placeholders
    "greeting": [
        "Hello",
        "Hi",
        "Hey",
        "Good morning",
        "Good afternoon",
        "What's up",
        "Greetings",
        "Howdy",
        "Yo",
        "Hi there",
        "Hey there",
    ],
    "joke_subject": [
        "programming",
        "math",
        "computers",
        "space",
        "science",
        "coffee",
        "physics",
        "chemistry",
        "bugs",
        "gpus",
        "keyboards",
        "monitors",
        "algorithms",
        "data science",
        "neural networks",
        "databases",
        "git",
        "compilers",
    ],
    "favorite_thing": [
        "color",
        "movie",
        "book",
        "programming language",
        "hobby",
        "video game",
        "music genre",
        "food",
        "animal",
        "sport",
        "season",
        "destination",
        "tech gadget",
        "historical figure",
        "scientific theory",
        "board game",
    ],
    "chat_topic": [
        "gaming",
        "artificial intelligence",
        "sports",
        "music",
        "cooking",
        "travel",
        "fitness",
        "movies",
        "podcasts",
        "virtual reality",
        "photography",
        "gardening",
        "space exploration",
        "history",
        "board games",
        "investing",
    ],
    "poem_subject": [
        "a lonely robot",
        "the autumn leaves",
        "coding at midnight",
        "a starry sky",
        "the ocean waves",
        "a forgotten library",
        "the first snow",
        "a cup of hot coffee",
        "sailing into the sunrise",
        "a crackling fireplace",
        "the city lights at dusk",
        "a flying paper airplane",
        "a quiet garden walk",
    ],
}

# Template patterns for each category
TEMPLATES = {
    "math": [
        "Solve the equation {num}{var} + {num} = {num}.",
        "What is the derivative of {math_func}?",
        "Calculate the integral of {poly} from {num} to {num}.",
        "Find the limit of {math_func} as {var} approaches {limit_target}.",
        "Find the eigenvalues of a {matrix_dim} matrix.",
        "Prove the validity of the {math_concept}.",
        "What is the sum of the interior angles in a {polygon}?",
        "Evaluate the sum of the geometric series: {series}.",
        "Solve the system of equations: {num}x + {num}y = {num} and {num}x - {num}y = {num}.",
        "What is the probability of {probability_event}?",
        "Simplify the algebraic expression: ({poly}) / ({var} - {num}).",
        "Find the vertex and focus of the parabola defined by y = {num}x^2 + {num}x.",
        "Calculate the dot product of vectors [{num}, {num}] and [{num}, {num}].",
        "If a right triangle has legs of length {num} and {num}, what is the hypotenuse?",
        "Determine if the series {series} converges or diverges.",
    ],
    "coding": [
        "Write a {lang} function to {algo}.",
        "How do I implement a {data_struct} in {lang}?",
        "Explain why my {lang} code is throwing a {error_type}.",
        "Create a REST API endpoint in {lang} using {framework}.",
        "Write a regular expression pattern in {lang} to match {probability_event}.",
        "How do I connect to a {db_type} database in {lang}?",
        "Optimize this {lang} loop for performance.",
        "What is the difference between {concept} and {concept} in {lang}?",
        "How do I handle concurrency in {lang} using {concurrency}?",
        "Write a unit test for a custom {data_struct} in {lang} using {test_framework}.",
        "How do I serialize a JSON object to a string in {lang}?",
        "Explain the concept of memory management in {lang}.",
        "How do I read a file line by line in {lang}?",
        "Show me how to make an asynchronous HTTP GET request in {lang} using {framework}.",
        "What is the best way to handle exceptions globally in a {framework} app written in {lang}?",
    ],
    "research": [
        "Summarize the major causes and outcomes of {history_event}.",
        "Explain the biological differences between {bio_term} and {bio_term}.",
        "What are the latest developments in the field of {science_field}?",
        "What are the primary factors behind {econ_term}?",
        "Compare and contrast {concept} and {concept}.",
        "Write a detailed summary of the scientific research on {science_field}.",
        "Explain the physics behind {science_field} in simple terms.",
        "What is the impact of {science_field} on modern society?",
        "Describe the cellular process of {bio_term}.",
        "What are the main ethical arguments regarding {ethical_issue}?",
        "Analyze the historical significance of {history_event} on world politics.",
        "Explain how the concept of {concept} differs from {concept} historically.",
        "Provide a comprehensive literature review of {science_field}.",
        "What are the long-term economic consequences of {econ_term}?",
        "How does {bio_term} play a role in evolutionary biology?",
    ],
    "casual_chat": [
        "{greeting}! How are you doing today?",
        "Tell me a funny joke about {joke_subject}.",
        "What is your favorite {favorite_thing}?",
        "Hey, let's chat about {chat_topic}.",
        "Who are you, and what can you help me with?",
        "Can you write a short poem about {poem_subject}?",
        "Give me some ideas of hobbies to pick up related to {chat_topic}.",
        "What is your opinion on the future of {science_field}?",
        "Good morning! Recommend a good {favorite_thing} for me to read.",
        "Tell me a story about a programmer who discovered {science_field}.",
        "What do you think is the meaning of life?",
        "Do you have any interesting facts to share about {joke_subject}?",
        "How was your day? Oh wait, you are an AI!",
        "Recommend some travel destinations for someone who loves {chat_topic}.",
        "If you could have any job in the world, what would it be?",
    ],
}


def generate_random_prompt(category: str) -> str:
    """Selects a random template and populates placeholders to create a unique prompt."""
    template = random.choice(TEMPLATES[category])

    # Find all placeholders in the template (e.g., {num}, {lang})
    placeholders_in_temp = [p.split("}")[0] for p in template.split("{")[1:]]

    replacements = {}
    for p in placeholders_in_temp:
        if p not in replacements:
            options = PLACEHOLDERS.get(p, ["placeholder"])
            replacements[p] = random.choice(options)
        else:
            # Handle duplicate placeholders in one template
            options = PLACEHOLDERS.get(p, ["placeholder"])
            val = random.choice(options)
            counter = 0
            while val == replacements[p] and counter < 20:
                val = random.choice(options)
                counter += 1
            replacements[p + "_2"] = val

    # Format the template
    formatted_prompt = template
    for key, val in replacements.items():
        if "_" in key:
            # Replace the second occurrence
            formatted_prompt = formatted_prompt.replace("{" + key.split("_")[0] + "}", val, 1)
        else:
            formatted_prompt = formatted_prompt.replace("{" + key + "}", val, 1)

    return formatted_prompt


def main():
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

    all_records = []
    total_target = 2000
    target_per_category = total_target // len(CATEGORIES)

    print(
        f"Generating synthetic dataset of {total_target} prompts ({target_per_category} per category)..."
    )

    # For reproducibility
    random.seed(42)

    for category in CATEGORIES:
        category_prompts = set()
        attempts = 0
        # Check attempts threshold
        max_attempts = target_per_category * 20

        while len(category_prompts) < target_per_category and attempts < max_attempts:
            attempts += 1
            prompt = generate_random_prompt(category)
            category_prompts.add(prompt)

        print(
            f"✓ Generated {len(category_prompts)} unique prompts for '{category}' (in {attempts} attempts)"
        )

        # Fallback: if we couldn't generate enough unique prompts, populate with duplicate selections
        prompts_list = list(category_prompts)
        if len(prompts_list) < target_per_category:
            needed = target_per_category - len(prompts_list)
            print(
                f"  - Padding category '{category}' with {needed} randomly repeated items to reach {target_per_category}"
            )
            for _ in range(needed):
                prompts_list.append(random.choice(prompts_list))

        for prompt in prompts_list:
            all_records.append({"prompt": prompt, "category": category})

    # Shuffle dataset to mix categories
    random.shuffle(all_records)

    print(f"\nWriting dataset to {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["prompt", "category"])
        for record in all_records:
            writer.writerow([record["prompt"], record["category"]])

    print(f"✓ Completed! Total rows written: {len(all_records)}")


if __name__ == "__main__":
    main()
