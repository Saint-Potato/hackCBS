import asyncio
import pytest
from database_connector import DatabaseConnector, DatabaseConfig, DatabaseType

class TestDatabaseConnector:
    """Test cases for database connector"""
    
    @pytest.mark.asyncio
    async def test_connector_initialization(self):
        """Test connector initialization"""
        connector = DatabaseConnector()
        assert connector.connections == {}
        assert connector.schemas == {}
    
    def test_database_config_creation(self):
        """Test database configuration creation"""
        config = DatabaseConfig(
            db_type=DatabaseType.MYSQL,
            host="localhost",
            port=3306,
            username="test",
            password="test",
            database="test_db"
        )
        
        assert config.db_type == DatabaseType.MYSQL
        assert config.host == "localhost"
        assert config.port == 3306
        assert config.username == "test"
        assert config.password == "test"
        assert config.database == "test_db"
    
    def test_config_to_dict(self):
        """Test config to dictionary conversion"""
        config = DatabaseConfig(
            db_type=DatabaseType.POSTGRESQL,
            host="localhost",
            port=5432,
            username="postgres",
            password="password",
            database="test_db"
        )
        
        config_dict = config.to_dict()
        expected = {
            "db_type": "postgresql",
            "host": "localhost",
            "port": 5432,
            "username": "postgres",
            "password": "password",
            "database": "test_db"
        }
        
        assert config_dict == expected
    
    @pytest.mark.asyncio
    async def test_invalid_database_type(self):
        """Test handling of invalid database type"""
        connector = DatabaseConnector()
        
        # This should raise an error due to invalid enum value
        with pytest.raises(ValueError):
            config = DatabaseConfig(
                db_type="invalid_type",  # This will fail at enum level
                host="localhost",
                port=3306,
                username="test",
                password="test",
                database="test_db"
            )

async def run_manual_tests():
    """Manual tests that can be run with actual database connections"""
    print("🧪 Running Manual Database Connection Tests")
    print("=" * 50)
    
    connector = DatabaseConnector()
    
    # Test configurations - UPDATE THESE WITH YOUR ACTUAL DATABASE CREDENTIALS
    test_configs = [
        # DatabaseConfig(
        #     db_type=DatabaseType.MYSQL,
        #     host="localhost",
        #     port=3306,
        #     username="root",
        #     password="your_password",
        #     database="test"
        # ),
        # DatabaseConfig(
        #     db_type=DatabaseType.POSTGRESQL,
        #     host="localhost",
        #     port=5432,
        #     username="postgres",
        #     password="your_password",
        #     database="test"
        # ),
        # DatabaseConfig(
        #     db_type=DatabaseType.MONGODB,
        #     host="localhost",
        #     port=27017,
        #     username="admin",
        #     password="your_password",
        #     database="test"
        # )
    ]
    
    if not test_configs:
        print("⚠️ No test configurations provided.")
        print("To run manual tests, uncomment and update the test_configs in test_connections.py")
        return
    
    for config in test_configs:
        print(f"\n🔄 Testing {config.db_type.value} connection...")
        
        try:
            result = await connector.test_connection(config)
            
            if result["success"]:
                print(f"✅ {result['message']}")
                
                # Test schema discovery
                print(f"🔍 Testing schema discovery for {config.db_type.value}...")
                schema = await connector.discover_schema(config.db_type)
                
                if schema:
                    print("✅ Schema discovery successful!")
                    summary = connector.get_schema_summary(config.db_type)
                    print(summary)
                else:
                    print("⚠️ Schema discovery returned empty results")
            else:
                print(f"❌ {result['message']}")
                
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
    
    # Clean up
    await connector.close_all_connections()
    print("\n✅ All tests completed and connections closed.")

if __name__ == "__main__":
    print("Choose test mode:")
    print("1. Unit tests (pytest)")
    print("2. Manual connection tests")
    
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
        # Run manual tests
        asyncio.run(run_manual_tests())
    else:
        print("Invalid choice")