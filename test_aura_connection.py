print("🔍 SIMPLE TEST")
print("=" * 20)

try:
    import os
    print("✅ os imported")
except Exception as e:
    print(f"❌ os import failed: {e}")

try:
    from dotenv import load_dotenv
    print("✅ dotenv imported")
except Exception as e:
    print(f"❌ dotenv import failed: {e}")

try:
    from neo4j import GraphDatabase
    print("✅ neo4j imported")
except Exception as e:
    print(f"❌ neo4j import failed: {e}")

try:
    load_dotenv()
    uri = os.getenv('NEO4J_URI')
    print(f"✅ Environment loaded")
    print(f"📍 URI: {uri[:20]}..." if uri else "❌ No URI found")
except Exception as e:
    print(f"❌ Environment load failed: {e}")