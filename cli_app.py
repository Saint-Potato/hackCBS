import asyncio
import sys
from typing import Optional
from database_connector import DatabaseConnector, DatabaseConfig, DatabaseType

class DatabaseCLI:
    """Command-line interface for database connections"""
    
    def __init__(self):
        self.connector = DatabaseConnector()
        self.current_connections = {}
    
    def display_welcome(self):
        """Display welcome message"""
        print("\n" + "="*60)
        print("🚀 AI-Driven DB RAG & Analytics - Database Connector")
        print("="*60)
        print("Connect to MySQL, PostgreSQL, and MongoDB databases")
        print("Discover schemas and analyze your data structure")
        print("="*60 + "\n")
    
    def display_menu(self):
        """Display main menu"""
        print("\n📋 Main Menu:")
        print("1. Connect to MySQL")
        print("2. Connect to PostgreSQL") 
        print("3. Connect to MongoDB")
        print("4. View Connected Databases")
        print("5. Discover Schema")
        print("6. View Schema Summary")
        print("7. Test Connection")
        print("8. Exit")
        print("-" * 40)
    
    def get_database_config(self, db_type: DatabaseType) -> Optional[DatabaseConfig]:
        """Get database configuration from user input"""
        print(f"\n🔧 Configure {db_type.value.upper()} Connection:")
        print("-" * 40)
        
        try:
            host = input("Host (default: localhost): ").strip() or "localhost"
            
            # Set default ports
            default_ports = {
                DatabaseType.MYSQL: 3306,
                DatabaseType.POSTGRESQL: 5432,
                DatabaseType.MONGODB: 27017
            }
            
            port_input = input(f"Port (default: {default_ports[db_type]}): ").strip()
            port = int(port_input) if port_input else default_ports[db_type]
            
            username = input("Username: ").strip()
            if not username:
                print("❌ Username is required!")
                return None
            
            password = input("Password: ").strip()
            if not password:
                print("❌ Password is required!")
                return None
            
            database = input("Database name: ").strip()
            if not database:
                print("❌ Database name is required!")
                return None
            
            return DatabaseConfig(
                db_type=db_type,
                host=host,
                port=port,
                username=username,
                password=password,
                database=database
            )
        
        except ValueError as e:
            print(f"❌ Invalid input: {e}")
            return None
        except KeyboardInterrupt:
            print("\n❌ Operation cancelled by user")
            return None
    
    async def connect_database(self, db_type: DatabaseType):
        """Connect to a database"""
        config = self.get_database_config(db_type)
        if not config:
            return
        
        print(f"\n🔄 Connecting to {db_type.value}...")
        
        try:
            result = await self.connector.test_connection(config)
            
            if result["success"]:
                print(f"✅ {result['message']}")
                self.current_connections[db_type.value] = config
                
                # Automatically discover schema
                print("🔍 Discovering schema...")
                schema = await self.connector.discover_schema(db_type)
                if schema:
                    print("✅ Schema discovered successfully!")
                    print(f"📊 Found {len(schema.get('tables', schema.get('collections', {})))} tables/collections")
                else:
                    print("⚠️ Schema discovery returned empty results")
            else:
                print(f"❌ {result['message']}")
                
        except Exception as e:
            print(f"❌ Connection failed: {e}")
    
    def view_connections(self):
        """Display current connections"""
        print("\n🔗 Current Database Connections:")
        print("-" * 40)
        
        if not self.current_connections:
            print("No active connections")
            return
        
        for db_type, config in self.current_connections.items():
            print(f"✅ {db_type.upper()}: {config.username}@{config.host}:{config.port}/{config.database}")
    
    async def discover_schema_menu(self):
        """Schema discovery menu"""
        if not self.current_connections:
            print("❌ No active connections. Please connect to a database first.")
            return
        
        print("\n🔍 Available databases for schema discovery:")
        db_types = list(self.current_connections.keys())
        
        for i, db_type in enumerate(db_types, 1):
            print(f"{i}. {db_type.upper()}")
        
        try:
            choice = int(input("\nSelect database (number): ")) - 1
            if 0 <= choice < len(db_types):
                db_type_str = db_types[choice]
                db_type = DatabaseType(db_type_str)
                
                print(f"🔄 Discovering schema for {db_type.value}...")
                schema = await self.connector.discover_schema(db_type)
                
                if schema:
                    print("✅ Schema discovery completed!")
                    summary = self.connector.get_schema_summary(db_type)
                    print(summary)
                else:
                    print("❌ Schema discovery failed or returned empty results")
            else:
                print("❌ Invalid selection")
        
        except (ValueError, KeyboardInterrupt):
            print("❌ Invalid input or operation cancelled")
    
    def view_schema_summary(self):
        """View schema summary for connected databases"""
        if not self.current_connections:
            print("❌ No active connections. Please connect to a database first.")
            return
        
        print("\n📊 Schema Summaries:")
        print("=" * 60)
        
        for db_type_str in self.current_connections.keys():
            db_type = DatabaseType(db_type_str)
            summary = self.connector.get_schema_summary(db_type)
            print(summary)
    
    async def test_connection_menu(self):
        """Test connection menu"""
        print("\n🧪 Test Database Connection:")
        print("1. Test MySQL")
        print("2. Test PostgreSQL")
        print("3. Test MongoDB")
        
        try:
            choice = int(input("Select database type (1-3): "))
            db_types = [DatabaseType.MYSQL, DatabaseType.POSTGRESQL, DatabaseType.MONGODB]
            
            if 1 <= choice <= 3:
                db_type = db_types[choice - 1]
                config = self.get_database_config(db_type)
                
                if config:
                    print(f"🔄 Testing {db_type.value} connection...")
                    result = await self.connector.test_connection(config)
                    
                    if result["success"]:
                        print(f"✅ {result['message']}")
                        print(f"📋 Connection Info: {result['connection_info']}")
                    else:
                        print(f"❌ {result['message']}")
            else:
                print("❌ Invalid selection")
        
        except (ValueError, KeyboardInterrupt):
            print("❌ Invalid input or operation cancelled")
    
    async def run(self):
        """Run the CLI application"""
        self.display_welcome()
        
        try:
            while True:
                self.display_menu()
                
                try:
                    choice = input("Enter your choice (1-8): ").strip()
                    
                    if choice == "1":
                        await self.connect_database(DatabaseType.MYSQL)
                    elif choice == "2":
                        await self.connect_database(DatabaseType.POSTGRESQL)
                    elif choice == "3":
                        await self.connect_database(DatabaseType.MONGODB)
                    elif choice == "4":
                        self.view_connections()
                    elif choice == "5":
                        await self.discover_schema_menu()
                    elif choice == "6":
                        self.view_schema_summary()
                    elif choice == "7":
                        await self.test_connection_menu()
                    elif choice == "8":
                        print("\n👋 Closing all connections...")
                        await self.connector.close_all_connections()
                        print("✅ All connections closed. Goodbye!")
                        break
                    else:
                        print("❌ Invalid choice. Please enter 1-8.")
                
                except KeyboardInterrupt:
                    print("\n\n👋 Exiting...")
                    await self.connector.close_all_connections()
                    break
                
                # Wait for user to continue
                input("\nPress Enter to continue...")
        
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
        finally:
            await self.connector.close_all_connections()

async def main():
    """Main entry point"""
    cli = DatabaseCLI()
    await cli.run()

if __name__ == "__main__":
    asyncio.run(main())