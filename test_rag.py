import asyncio
import pytest
from schema_rag import SchemaRAG, DatabaseConnectorWithRAG
from database_connector import DatabaseType, DatabaseConfig
import tempfile
import shutil
import os

class TestSchemaRAG:
    """Test cases for Schema RAG functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.rag = SchemaRAG(persist_directory=self.temp_dir)
    
    def teardown_method(self):
        """Cleanup test environment"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_rag_initialization(self):
        """Test RAG system initialization"""
        assert self.rag is not None
        assert self.rag.collection is not None
        assert self.rag.embedding_model is not None
    
    def test_embedding_generation(self):
        """Test embedding generation"""
        text = "This is a test table with user information"
        embedding = self.rag._generate_embedding(text)
        
        assert isinstance(embedding, list)
        assert len(embedding) > 0
        assert all(isinstance(x, float) for x in embedding)
    
    @pytest.mark.asyncio
    async def test_store_mysql_schema(self):
        """Test storing MySQL schema"""
        # Sample MySQL schema
        schema = {
            "tables": {
                "users": {
                    "columns": [
                        {"name": "id", "type": "int", "null": False, "key": "PRI", "default": None, "extra": "auto_increment"},
                        {"name": "email", "type": "varchar(255)", "null": False, "key": "", "default": None, "extra": ""},
                        {"name": "name", "type": "varchar(100)", "null": True, "key": "", "default": None, "extra": ""}
                    ],
                    "primary_keys": ["id"],
                    "indexes": []
                }
            },
            "relationships": []
        }
        
        db_config = {
            "database": "test_db",
            "host": "localhost",
            "port": "3306"
        }
        
        success = await self.rag.store_schema(schema, DatabaseType.MYSQL, db_config)
        assert success
    
    @pytest.mark.asyncio
    async def test_store_mongodb_schema(self):
        """Test storing MongoDB schema"""
        # Sample MongoDB schema
        schema = {
            "collections": {
                "products": {
                    "document_count": 1000,
                    "fields": {
                        "_id": {"types": ["ObjectId"], "count": 1000, "null_count": 0},
                        "name": {"types": ["str"], "count": 1000, "null_count": 0},
                        "price": {"types": ["float", "int"], "count": 995, "null_count": 5},
                        "category": {"types": ["str"], "count": 980, "null_count": 20}
                    },
                    "indexes": []
                }
            }
        }
        
        db_config = {
            "database": "test_db",
            "host": "localhost",
            "port": "27017"
        }
        
        success = await self.rag.store_schema(schema, DatabaseType.MONGODB, db_config)
        assert success
    
    def test_schema_search(self):
        """Test schema search functionality"""
        # First, we need to store some data
        # This test would work better as an integration test with actual data
        
        # Test empty search
        results = self.rag.search_schema("test query")
        assert isinstance(results, list)
    
    def test_database_overview(self):
        """Test database overview"""
        overview = self.rag.get_database_overview()
        
        assert isinstance(overview, dict)
        assert "total_documents" in overview
        assert "databases" in overview
        assert "document_types" in overview

async def run_integration_tests():
    """Integration tests with actual schema data"""
    print("🧪 Running Schema RAG Integration Tests")
    print("=" * 50)
    
    # Create temporary RAG instance
    temp_dir = tempfile.mkdtemp()
    rag = SchemaRAG(persist_directory=temp_dir)
    
    try:
        # Test 1: Store sample schemas
        print("1. Testing schema storage...")
        
        # MySQL schema
        mysql_schema = {
            "tables": {
                "customers": {
                    "columns": [
                        {"name": "customer_id", "type": "int", "null": False, "key": "PRI", "default": None, "extra": "auto_increment"},
                        {"name": "email", "type": "varchar(255)", "null": False, "key": "UNI", "default": None, "extra": ""},
                        {"name": "first_name", "type": "varchar(100)", "null": False, "key": "", "default": None, "extra": ""},
                        {"name": "last_name", "type": "varchar(100)", "null": False, "key": "", "default": None, "extra": ""},
                        {"name": "created_at", "type": "timestamp", "null": False, "key": "", "default": "CURRENT_TIMESTAMP", "extra": ""}
                    ],
                    "primary_keys": ["customer_id"],
                    "indexes": []
                },
                "orders": {
                    "columns": [
                        {"name": "order_id", "type": "int", "null": False, "key": "PRI", "default": None, "extra": "auto_increment"},
                        {"name": "customer_id", "type": "int", "null": False, "key": "MUL", "default": None, "extra": ""},
                        {"name": "total_amount", "type": "decimal(10,2)", "null": False, "key": "", "default": None, "extra": ""},
                        {"name": "status", "type": "enum('pending','completed','cancelled')", "null": False, "key": "", "default": "pending", "extra": ""},
                        {"name": "order_date", "type": "date", "null": False, "key": "", "default": None, "extra": ""}
                    ],
                    "primary_keys": ["order_id"],
                    "indexes": []
                }
            },
            "relationships": [
                {
                    "from_table": "orders",
                    "from_column": "customer_id",
                    "to_table": "customers",
                    "to_column": "customer_id"
                }
            ]
        }
        
        db_config = {
            "database": "ecommerce_db",
            "host": "localhost",
            "port": "3306"
        }
        
        success = await rag.store_schema(mysql_schema, DatabaseType.MYSQL, db_config)
        print(f"   MySQL schema storage: {'✅' if success else '❌'}")
        
        # MongoDB schema
        mongo_schema = {
            "collections": {
                "user_profiles": {
                    "document_count": 5000,
                    "fields": {
                        "_id": {"types": ["ObjectId"], "count": 5000, "null_count": 0},
                        "username": {"types": ["str"], "count": 5000, "null_count": 0},
                        "email": {"types": ["str"], "count": 5000, "null_count": 0},
                        "profile.age": {"types": ["int"], "count": 4800, "null_count": 200},
                        "profile.location": {"types": ["str"], "count": 4500, "null_count": 500},
                        "preferences": {"types": ["array"], "count": 4900, "null_count": 100},
                        "created_date": {"types": ["datetime"], "count": 5000, "null_count": 0}
                    },
                    "indexes": []
                },
                "analytics_events": {
                    "document_count": 100000,
                    "fields": {
                        "_id": {"types": ["ObjectId"], "count": 100000, "null_count": 0},
                        "event_type": {"types": ["str"], "count": 100000, "null_count": 0},
                        "user_id": {"types": ["ObjectId"], "count": 95000, "null_count": 5000},
                        "timestamp": {"types": ["datetime"], "count": 100000, "null_count": 0},
                        "properties": {"types": ["object"], "count": 98000, "null_count": 2000}
                    },
                    "indexes": []
                }
            }
        }
        
        mongo_config = {
            "database": "analytics_db",
            "host": "localhost",
            "port": "27017"
        }
        
        success = await rag.store_schema(mongo_schema, DatabaseType.MONGODB, mongo_config)
        print(f"   MongoDB schema storage: {'✅' if success else '❌'}")
        
        # Test 2: Search functionality
        print("\n2. Testing schema search...")
        
        test_queries = [
            "Find tables with customer information",
            "What fields store email addresses?",
            "Show me order related data",
            "Find all user profile fields",
            "What collections have timestamp data?",
            "Show me foreign key relationships"
        ]
        
        for query in test_queries:
            results = rag.search_schema(query, n_results=3)
            print(f"   Query: '{query}' -> {len(results)} results")
        
        # Test 3: Overview
        print("\n3. Testing system overview...")
        overview = rag.get_database_overview()
        print(f"   Total documents: {overview['total_documents']}")
        print(f"   Databases: {len(overview['databases'])}")
        print(f"   Document types: {overview['document_types']}")
        
        print("\n✅ All integration tests completed!")
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
    finally:
        # Cleanup
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

if __name__ == "__main__":
    import sys
    
    print("Choose test mode:")
    print("1. Unit tests (pytest)")
    print("2. Integration tests")
    
    choice = input("Enter choice (1 or 2): ").strip()
    
    if choice == "1":
        # Run pytest
        import subprocess
        result = subprocess.run(["python", "-m", "pytest", __file__, "-v"], 
                              capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print("Errors:", result.stderr)
    elif choice == "2":
        # Run integration tests
        asyncio.run(run_integration_tests())
    else:
        print("Invalid choice")