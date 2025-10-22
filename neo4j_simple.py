import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

# Test basic connection
uri = os.getenv('NEO4J_URI')
user = os.getenv('NEO4J_USER') 
password = os.getenv('NEO4J_PASSWORD')

print(f"URI: {uri}")
print(f"User: {user}")
print(f"Password: {'*' * len(password) if password else 'None'}")

try:
    driver = GraphDatabase.driver(uri, auth=(user, password))
    with driver.session() as session:
        result = session.run("RETURN 'Hello Neo4j!' as message")
        record = result.single()
        print(f"✅ Connection successful: {record['message']}")
    driver.close()
except Exception as e:
    print(f"❌ Connection failed: {e}")