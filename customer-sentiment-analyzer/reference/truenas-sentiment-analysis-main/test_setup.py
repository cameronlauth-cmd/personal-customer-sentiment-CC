import sys
import os

print(f"Python: {sys.version}")

try:
    import anthropic
    print("✓ Anthropic SDK installed")
    
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if api_key and api_key.startswith("sk-"):
        print(f"✓ API key loaded: {api_key[:20]}...")
    else:
        print("✗ API key not found in .env")
        
    import pandas as pd
    print("✓ Pandas installed")
    
    import matplotlib
    print("✓ Matplotlib installed")
    
    print("\n🎉 All systems go!")
    
except Exception as e:
    print(f"✗ Error: {e}")
