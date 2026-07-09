import os
import sys
import asyncio

# Add project root directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.ollama_client import OllamaClient
from app.services.fireworks_client import FireworksClient
from app.database import get_aggregate_metrics

async def check_systems():
    print("Checking system status...")
    
    # 1. Check Ollama
    print("1. Testing Ollama connection...", end="")
    ollama_ok = await OllamaClient.check_health()
    if ollama_ok:
        print(" [✓ CONNECTED]")
    else:
        print(" [✗ DISCONNECTED] - Make sure Ollama is serving at http://localhost:11434")

    # 2. Check Fireworks API
    print("2. Testing Fireworks API connectivity...", end="")
    fireworks_ok = await FireworksClient.check_health()
    if fireworks_ok:
        print(" [✓ CONNECTED]")
    else:
        print(" [✗ DISCONNECTED] - Verify FIREWORKS_API_KEY is configured in .env")

    # 3. Check SQLite DB
    print("3. Checking SQLite DB state...", end="")
    db_ok = False
    try:
        metrics = get_aggregate_metrics()
        db_ok = True
        print(" [✓ HEALTHY]")
    except Exception as e:
        print(f" [✗ ERROR] - {e}")
        
    print("\n--- Summary ---")
    if ollama_ok and fireworks_ok and db_ok:
        print("All dependencies are operational! Ready to run.")
        sys.exit(0)
    else:
        print("Some dependencies are down. Please check instructions in Setup Guide.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(check_systems())
