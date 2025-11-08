import asyncio
import asyncpg
import aiomysql
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from typing import Dict, Any, Optional, Union, List
import json
from dataclasses import dataclass
from enum import Enum
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseType(Enum):
    MYSQL = "mysql"
    POSTGRESQL = "postgresql"
    MONGODB = "mongodb"

@dataclass
class DatabaseConfig:
    """Database connection configuration"""
    db_type: DatabaseType
    host: str
    port: int
    username: str
    password: str
    database: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "db_type": self.db_type.value,
            "host": self.host,
            "port": self.port,
            "username": self.username,
            "password": self.password,
            "database": self.database
        }

class DatabaseConnector:
    """Universal database connector for MySQL, PostgreSQL, and MongoDB"""
    
    def __init__(self):
        self.connections = {}
        self.schemas = {}
    
    async def connect(self, config: DatabaseConfig) -> bool:
        """Connect to database based on type"""
        try:
            if config.db_type == DatabaseType.MYSQL:
                return await self._connect_mysql(config)
            elif config.db_type == DatabaseType.POSTGRESQL:
                return await self._connect_postgresql(config)
            elif config.db_type == DatabaseType.MONGODB:
                return await self._connect_mongodb(config)
            else:
                raise ValueError(f"Unsupported database type: {config.db_type}")
        except Exception as e:
            logger.error(f"Failed to connect to {config.db_type.value}: {e}")
            return False
    
    async def _connect_mysql(self, config: DatabaseConfig) -> bool:
        """Connect to MySQL database"""
        try:
            # Create connection pool
            pool = await aiomysql.create_pool(
                host=config.host,
                port=config.port,
                user=config.username,
                password=config.password,
                db=config.database,
                charset='utf8mb4',
                autocommit=True,
                minsize=1,
                maxsize=10
            )
            
            # Test connection
            async with pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute("SELECT 1")
                    result = await cursor.fetchone()
                    if result[0] == 1:
                        self.connections[config.db_type.value] = pool
                        logger.info(f"Successfully connected to MySQL: {config.host}:{config.port}/{config.database}")
                        return True
            return False
        except Exception as e:
            logger.error(f"MySQL connection failed: {e}")
            return False
    
    async def _connect_postgresql(self, config: DatabaseConfig) -> bool:
        """Connect to PostgreSQL database"""
        try:
            # Create connection string
            connection_string = f"postgresql://{config.username}:{config.password}@{config.host}:{config.port}/{config.database}"
            
            # Test connection
            conn = await asyncpg.connect(connection_string)
            result = await conn.fetchval("SELECT 1")
            if result == 1:
                await conn.close()
                
                # Create connection pool
                pool = await asyncpg.create_pool(connection_string, min_size=1, max_size=10)
                self.connections[config.db_type.value] = pool
                logger.info(f"Successfully connected to PostgreSQL: {config.host}:{config.port}/{config.database}")
                return True
            return False
        except Exception as e:
            logger.error(f"PostgreSQL connection failed: {e}")
            return False
    
    async def _connect_mongodb(self, config: DatabaseConfig) -> bool:
        """Connect to MongoDB database"""
        try:
            # Create connection string
            connection_string = f"mongodb://{config.username}:{config.password}@{config.host}:{config.port}/{config.database}"
            
            # Create client
            client = AsyncIOMotorClient(connection_string)
            
            # Test connection
            await client.admin.command('ping')
            
            self.connections[config.db_type.value] = client
            logger.info(f"Successfully connected to MongoDB: {config.host}:{config.port}/{config.database}")
            return True
        except Exception as e:
            logger.error(f"MongoDB connection failed: {e}")
            return False
    
    async def discover_schema(self, db_type: DatabaseType) -> Dict[str, Any]:
        """Discover database schema"""
        try:
            if db_type == DatabaseType.MYSQL:
                return await self._discover_mysql_schema()
            elif db_type == DatabaseType.POSTGRESQL:
                return await self._discover_postgresql_schema()
            elif db_type == DatabaseType.MONGODB:
                return await self._discover_mongodb_schema()
            else:
                raise ValueError(f"Unsupported database type: {db_type}")
                
        except Exception as e:
            logger.error(f"Error discovering schema: {e}")
            return None
    
    async def _discover_mysql_schema(self) -> Dict[str, Any]:
        """Discover MySQL schema"""
        pool = self.connections.get("mysql")
        if not pool:
            raise Exception("MySQL connection not established")
        
        schema = {
            "tables": {},
            "relationships": []
        }
        
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("SELECT DATABASE()")
                database = (await cursor.fetchone())[0]

                await cursor.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = %s
                """, (database,))
                tables = [row[0] for row in await cursor.fetchall()]

                for table in tables:
                    await cursor.execute("""
                        SELECT column_name, data_type, is_nullable, column_key, column_default, extra
                        FROM information_schema.columns
                        WHERE table_schema = %s AND table_name = %s
                        ORDER BY ordinal_position
                    """, (database, table))
                    columns = []
                    primary_keys = []

                    for col in await cursor.fetchall():
                        column = {
                            "name": col[0],
                            "type": col[1],
                            "null": col[2] == "YES",
                            "key": col[3],
                            "default": col[4],
                            "extra": col[5]
                        }
                        columns.append(column)
                        if col[3] == "PRI":
                            primary_keys.append(col[0])

                    schema["tables"][table] = {
                        "columns": columns,
                        "primary_keys": primary_keys
                    }

                await cursor.execute("""
                    SELECT 
                        table_name,
                        column_name,
                        referenced_table_name,
                        referenced_column_name
                    FROM information_schema.key_column_usage
                    WHERE table_schema = %s
                    AND referenced_table_name IS NOT NULL
                """, (database,))

                for rel in await cursor.fetchall():
                    schema["relationships"].append({
                        "from_table": rel[0],
                        "from_column": rel[1],
                        "to_table": rel[2],
                        "to_column": rel[3]
                    })

        return schema
    
    async def _discover_postgresql_schema(self) -> Dict[str, Any]:
        """Discover PostgreSQL schema"""
        schema = {"tables": {}, "relationships": []}
        pool = self.connections.get("postgresql")
        
        if not pool:
            return schema
        
        async with pool.acquire() as conn:
            # Get all tables
            tables = await conn.fetch("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
            """)
            
            for table in tables:
                table_name = table['table_name']
                
                # Get columns
                columns = await conn.fetch("""
                    SELECT 
                        column_name,
                        data_type,
                        is_nullable,
                        column_default,
                        character_maximum_length
                    FROM information_schema.columns
                    WHERE table_name = $1 AND table_schema = 'public'
                    ORDER BY ordinal_position
                """, table_name)
                
                schema["tables"][table_name] = {
                    "columns": [],
                    "primary_keys": [],
                    "indexes": []
                }
                
                for column in columns:
                    column_info = {
                        "name": column['column_name'],
                        "type": column['data_type'],
                        "null": column['is_nullable'] == 'YES',
                        "default": column['column_default'],
                        "max_length": column['character_maximum_length']
                    }
                    schema["tables"][table_name]["columns"].append(column_info)
                
                # Get primary keys
                primary_keys = await conn.fetch("""
                    SELECT column_name
                    FROM information_schema.table_constraints tc
                    JOIN information_schema.key_column_usage kcu 
                        ON tc.constraint_name = kcu.constraint_name
                    WHERE tc.table_name = $1 AND tc.constraint_type = 'PRIMARY KEY'
                """, table_name)
                
                schema["tables"][table_name]["primary_keys"] = [pk['column_name'] for pk in primary_keys]
            
            # Get foreign key relationships
            relationships = await conn.fetch("""
                SELECT
                    tc.table_name,
                    kcu.column_name,
                    ccu.table_name AS referenced_table,
                    ccu.column_name AS referenced_column
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu 
                    ON tc.constraint_name = kcu.constraint_name
                JOIN information_schema.constraint_column_usage ccu 
                    ON ccu.constraint_name = tc.constraint_name
                WHERE tc.constraint_type = 'FOREIGN KEY'
            """)
            
            for rel in relationships:
                schema["relationships"].append({
                    "from_table": rel['table_name'],
                    "from_column": rel['column_name'],
                    "to_table": rel['referenced_table'],
                    "to_column": rel['referenced_column']
                })
        
        self.schemas["postgresql"] = schema
        return schema
    
    async def _discover_mongodb_schema(self) -> Dict[str, Any]:
        """Discover MongoDB schema"""
        schema = {"collections": {}}
        client = self.connections.get("mongodb")
        
        if not client:
            return schema
        
        # Get database from connection (assuming it's set in connection string)
        db = client.get_default_database()
        
        # Get all collections
        collections = await db.list_collection_names()
        
        for collection_name in collections:
            collection = db[collection_name]
            
            # Sample documents to infer schema
            sample_docs = []
            async for doc in collection.find().limit(100):
                sample_docs.append(doc)
            
            if sample_docs:
                # Analyze field types and structure
                field_analysis = {}
                for doc in sample_docs:
                    self._analyze_document_fields(doc, field_analysis)
                
                schema["collections"][collection_name] = {
                    "document_count": await collection.count_documents({}),
                    "fields": field_analysis,
                    "indexes": []
                }
                
                # Get indexes
                indexes = []
                async for index in collection.list_indexes():
                    indexes.append(index)
                schema["collections"][collection_name]["indexes"] = indexes
        
        self.schemas["mongodb"] = schema
        return schema
    
    def _analyze_document_fields(self, doc: Dict, field_analysis: Dict, prefix: str = ""):
        """Recursively analyze MongoDB document fields"""
        for key, value in doc.items():
            full_key = f"{prefix}.{key}" if prefix else key
            
            if full_key not in field_analysis:
                field_analysis[full_key] = {
                    "types": set(),
                    "count": 0,
                    "null_count": 0
                }
            
            field_analysis[full_key]["count"] += 1
            
            if value is None:
                field_analysis[full_key]["null_count"] += 1
                field_analysis[full_key]["types"].add("null")
            elif isinstance(value, dict):
                field_analysis[full_key]["types"].add("object")
                self._analyze_document_fields(value, field_analysis, full_key)
            elif isinstance(value, list):
                field_analysis[full_key]["types"].add("array")
                if value:  # Analyze first element if array is not empty
                    self._analyze_document_fields({"[0]": value[0]}, field_analysis, full_key)
            else:
                field_analysis[full_key]["types"].add(type(value).__name__)
        
        # Convert sets to lists for JSON serialization
        for field_info in field_analysis.values():
            if isinstance(field_info["types"], set):
                field_info["types"] = list(field_info["types"])
    
    def get_schema_summary(self, db_type: DatabaseType) -> str:
        """Get a human-readable schema summary"""
        schema = self.schemas.get(db_type.value, {})
        
        if not schema:
            return f"No schema available for {db_type.value}"
        
        if db_type in [DatabaseType.MYSQL, DatabaseType.POSTGRESQL]:
            tables = schema.get("tables", {})
            relationships = schema.get("relationships", [])
            
            summary = f"\n=== {db_type.value.upper()} SCHEMA SUMMARY ===\n"
            summary += f"Tables: {len(tables)}\n"
            summary += f"Relationships: {len(relationships)}\n\n"
            
            for table_name, table_info in tables.items():
                summary += f"📊 Table: {table_name}\n"
                summary += f"   Columns: {len(table_info['columns'])}\n"
                summary += f"   Primary Keys: {', '.join(table_info['primary_keys']) or 'None'}\n"
                
                for col in table_info['columns'][:5]:  # Show first 5 columns
                    summary += f"   - {col['name']} ({col['type']})\n"
                
                if len(table_info['columns']) > 5:
                    summary += f"   ... and {len(table_info['columns']) - 5} more columns\n"
                summary += "\n"
        
        elif db_type == DatabaseType.MONGODB:
            collections = schema.get("collections", {})
            summary = f"\n=== MONGODB SCHEMA SUMMARY ===\n"
            summary += f"Collections: {len(collections)}\n\n"
            
            for collection_name, collection_info in collections.items():
                summary += f"📄 Collection: {collection_name}\n"
                summary += f"   Documents: {collection_info['document_count']}\n"
                summary += f"   Fields: {len(collection_info['fields'])}\n"
                
                for field_name, field_info in list(collection_info['fields'].items())[:5]:
                    types = ', '.join(field_info['types'])
                    summary += f"   - {field_name} ({types})\n"
                
                if len(collection_info['fields']) > 5:
                    summary += f"   ... and {len(collection_info['fields']) - 5} more fields\n"
                summary += "\n"
        
        return summary
    
    async def test_connection(self, config: DatabaseConfig) -> Dict[str, Any]:
        """Test database connection and return status"""
        result = {
            "success": False,
            "message": "",
            "connection_info": {}
        }
        
        try:
            success = await self.connect(config)
            if success:
                result["success"] = True
                result["message"] = f"Successfully connected to {config.db_type.value}"
                result["connection_info"] = {
                    "host": config.host,
                    "port": config.port,
                    "database": config.database,
                    "type": config.db_type.value
                }
            else:
                result["message"] = f"Failed to connect to {config.db_type.value}"
        except Exception as e:
            result["message"] = f"Connection error: {str(e)}"
        
        return result
    
    async def close_all_connections(self):
        """Close all database connections"""
        for db_type, connection in self.connections.items():
            try:
                if db_type == "mysql":
                    connection.close()
                    await connection.wait_closed()
                elif db_type == "postgresql":
                    await connection.close()
                elif db_type == "mongodb":
                    connection.close()
                logger.info(f"Closed {db_type} connection")
            except Exception as e:
                logger.error(f"Error closing {db_type} connection: {e}")
        
        self.connections.clear()
        self.schemas.clear()

# Example usage and testing
async def main():
    """Example usage of the database connector"""
    connector = DatabaseConnector()
    
    # Example configurations (replace with actual credentials)
    configs = [
        # DatabaseConfig(
        #     db_type=DatabaseType.MYSQL,
        #     host="localhost",
        #     port=3306,
        #     username="root",
        #     password="password",
        #     database="test_db"
        # ),
        # DatabaseConfig(
        #     db_type=DatabaseType.POSTGRESQL,
        #     host="localhost",
        #     port=5432,
        #     username="postgres",
        #     password="password",
        #     database="test_db"
        # ),
        # DatabaseConfig(
        #     db_type=DatabaseType.MONGODB,
        #     host="localhost",
        #     port=27017,
        #     username="admin",
        #     password="password",
        #     database="test_db"
        # )
    ]
    
    print("=== Database Connector Test ===\n")
    
    # Test connections
    for config in configs:
        print(f"Testing {config.db_type.value} connection...")
        result = await connector.test_connection(config)
        print(f"Result: {result['message']}\n")
        
        if result["success"]:
            # Discover schema
            print(f"Discovering {config.db_type.value} schema...")
            schema = await connector.discover_schema(config.db_type)
            print(connector.get_schema_summary(config.db_type))
    
    # Close all connections
    await connector.close_all_connections()
    print("All connections closed.")

if __name__ == "__main__":
    asyncio.run(main())