import asyncio
from schema_rag import DatabaseConnectorWithRAG
from database_connector import DatabaseType, DatabaseConfig

async def test_rag_fix():
    """Test the RAG fix with sample data"""
    print("🔧 Testing ChromaDB metadata fix...")
    
    connector = DatabaseConnectorWithRAG()
    
    # Create a sample schema that would have caused the error
    sample_schema = {
        "tables": {
            "students": {
                "columns": [
                    {"name": "student_id", "type": "int", "null": False, "key": "PRI", "default": None, "extra": "auto_increment"},
                    {"name": "name", "type": "varchar(100)", "null": False, "key": "", "default": None, "extra": ""},
                    {"name": "email", "type": "varchar(255)", "null": True, "key": "", "default": None, "extra": ""}
                ],
                "primary_keys": ["student_id"],  # This was causing the error
                "indexes": []
            },
            "courses": {
                "columns": [
                    {"name": "course_id", "type": "int", "null": False, "key": "PRI", "default": None, "extra": "auto_increment"},
                    {"name": "course_name", "type": "varchar(200)", "null": False, "key": "", "default": None, "extra": ""},
                    {"name": "credits", "type": "int", "null": False, "key": "", "default": "3", "extra": ""}
                ],
                "primary_keys": ["course_id"],
                "indexes": []
            }
        },
        "relationships": [
            {
                "from_table": "enrollments",
                "from_column": "student_id",
                "to_table": "students",
                "to_column": "student_id"
            }
        ]
    }
    
    db_config = {
        "database": "school_db",
        "host": "localhost",
        "port": "3306"
    }
    
    # Test storing the schema
    success = await connector.rag.store_schema(sample_schema, DatabaseType.MYSQL, db_config)
    
    if success:
        print("✅ Schema stored successfully!")
        
        # Test the overview
        overview = connector.get_rag_overview()
        print(f"📊 Total documents: {overview['total_documents']}")
        print(f"📊 Databases: {list(overview['databases'].keys())}")
        
        # Test searching
        print("\n🔍 Testing search functionality...")
        test_queries = [
            "Find tables with student information",
            "What are the primary keys?",
            "Show me course related data",
            "Find email columns"
        ]
        
        for query in test_queries:
            results = connector.rag.search_schema(query, n_results=2)
            print(f"   Query: '{query}' -> {len(results)} results")
            
            if results:
                for result in results[:1]:  # Show first result
                    print(f"      Type: {result['metadata'].get('type')}")
                    print(f"      Relevance: {result['relevance']}")
                    print(f"      Content: {result['content'][:100]}...")
    else:
        print("❌ Failed to store schema")
    
    print("\n✅ Test completed!")

if __name__ == "__main__":
    asyncio.run(test_rag_fix())