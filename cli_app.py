from typing import Optional, Dict, Any, List  # Add List to the imports
import asyncio
import sys
from typing import Optional, Dict, Any, List  # Add List to imports
from database_connector import DatabaseType, DatabaseConfig
from enhanced_schema_rag import EnhancedDatabaseConnectorWithRAG
import json
from gemini_helper import GeminiHelper


class EnhancedDatabaseCLI:
    """Enhanced CLI with improved RAG capabilities"""

    def __init__(self):
        self.connector = EnhancedDatabaseConnectorWithRAG()
        self.current_connections = {}
        self.gemini = GeminiHelper()

    def display_welcome(self):
        """Display welcome message"""
        print("\n" + "=" * 75)
        print("🚀 AI-Driven DB RAG & Analytics - Enhanced Database Connector")
        print("=" * 75)
        print("Connect to MySQL, PostgreSQL, and MongoDB databases")
        print("Discover schemas and store them in ChromaDB for intelligent RAG")
        print("Ask questions about your database schema in natural language")
        print("=" * 75 + "\n")

    def display_menu(self):
        """Display main menu"""
        print("\n📋 Main Menu:")
        print("1. Connect to MySQL")
        print("2. Connect to PostgreSQL")
        print("3. Connect to MongoDB")
        print("4. View Connected Databases")
        print("5. Discover & Store Schema in RAG")
        print("6. View Schema Summary")
        print("7. 🧠 Ask Schema Questions (Natural Language)")
        print("8. View RAG System Overview")
        print("9. Test Schema Search")
        print("10. Reset RAG Collection")
        print("11. Exit")
        print("-" * 40)

    def get_database_config(self, db_type: DatabaseType) -> Optional[DatabaseConfig]:
        """Get database configuration from user input"""
        print(f"\n🔧 Configure {db_type.value.upper()} Connection:")
        print("-" * 40)

        try:
            host = input("Host (default: localhost): ").strip() or "localhost"

            default_ports = {
                DatabaseType.MYSQL: 3306,
                DatabaseType.POSTGRESQL: 5432,
                DatabaseType.MONGODB: 27017,
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
                database=database,
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
            print(
                f"✅ {db_type.upper()}: {config.username}@{config.host}:{config.port}/{config.database}"
            )

    async def discover_and_store_schema(self):
        """Discover schema and store in RAG system"""
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
                config = self.current_connections[db_type_str]

                print(f"🔄 Discovering and storing schema for {db_type.value}...")

                config_dict = {
                    "database": config.database,
                    "host": config.host,
                    "port": config.port,
                }

                schema = await self.connector.discover_and_store_schema(
                    db_type, config_dict
                )

                if schema:
                    print("✅ Schema discovery and RAG storage completed!")

                    if db_type in [DatabaseType.MYSQL, DatabaseType.POSTGRESQL]:
                        tables_count = len(schema.get("tables", {}))
                        relationships_count = len(schema.get("relationships", []))
                        print(
                            f"📊 Stored {tables_count} tables and {relationships_count} relationships in RAG system"
                        )
                    else:
                        collections_count = len(schema.get("collections", {}))
                        print(
                            f"📊 Stored {collections_count} collections in RAG system"
                        )
                else:
                    print("❌ Schema discovery failed")
            else:
                print("❌ Invalid selection")

        except (ValueError, KeyboardInterrupt):
            print("❌ Invalid input or operation cancelled")

    def view_schema_summary(self):
        """View schema summary for connected databases"""
        overview = self.connector.get_rag_overview()

        if overview["total_documents"] == 0:
            print(
                "❌ No schemas stored in RAG system. Please discover and store schemas first."
            )
            return

        print("\n📊 Schema Summaries:")
        print("=" * 60)

        # Show summary for all database types found in RAG
        db_types_in_rag = set()
        for db_info in overview["databases"].values():
            db_types_in_rag.add(db_info["type"])

        if not db_types_in_rag:
            print("No database schemas found in RAG system.")
            return

        for db_type_str in db_types_in_rag:
            try:
                db_type = DatabaseType(db_type_str)
                summary = self.connector.get_schema_summary(db_type)
                print(summary)
            except ValueError:
                print(f"❌ Unknown database type: {db_type_str}")

    def ask_schema_questions(self):
        """Enhanced natural language schema questions"""
        print("\n🧠 Ask Questions About Your Database Schema:")
        print("=" * 50)

        overview = self.connector.get_rag_overview()
        if overview["total_documents"] == 0:
            print(
                "❌ No schemas stored in RAG system. Please discover and store schemas first."
            )
            return

        print(f"📊 RAG System Status:")
        print(f"   • {overview['total_documents']} schema documents indexed")
        print(
            f"   • {len(overview['databases'])} database(s): {', '.join(overview['databases'].keys())}"
        )
        print()

        # Show example questions
        print("💡 Example Questions:")
        print("   • How many tables are there?")
        print("   • What tables store student information?")
        print("   • Find all email columns")
        print("   • Show me foreign key relationships")
        print("   • What's the structure of the users table?")
        print("   • Which fields can be null?")
        print()

        try:
            query = input("🤔 Your question: ").strip()
            if not query:
                print("❌ Question cannot be empty")
                return

            # Optional database filter
            if len(overview["databases"]) > 1:
                print(
                    f"\nAvailable databases: {', '.join(overview['databases'].keys())}"
                )
                database_filter = input(
                    "Focus on specific database (optional): "
                ).strip()
                database_filter = database_filter if database_filter else None
            else:
                database_filter = None

            print(f"\n🔄 Analyzing: '{query}'...")

            # Search schema with enhanced system
            results = self.connector.rag.search_schema(
                query=query, n_results=5, database_filter=database_filter
            )

            if results:
                # Check if it's a direct metadata answer
                if results[0]["metadata"].get("type") == "metadata_answer":
                    print(f"\n💡 Answer:")
                    print(f"   {results[0]['content']}")

                    if "details" in results[0]:
                        details = results[0]["details"]
                        if "tables" in details:
                            print(f"\n📋 Tables: {', '.join(details['tables'])}")
                        if "breakdown" in details:
                            print(f"\n📊 Breakdown by database:")
                            for db, count in details["breakdown"].items():
                                print(f"   • {db}: {count} tables")
                else:
                    print(f"\n🎯 Found {len(results)} relevant results:")
                    print("=" * 50)

                    for i, result in enumerate(results, 1):
                        print(
                            f"\n📋 Result {i} - {result['relevance'].title()} Relevance (Score: {result['similarity_score']:.3f})"
                        )

                        metadata = result["metadata"]
                        print(
                            f"   Database: {metadata.get('database_name', 'unknown')}"
                        )
                        print(f"   Type: {metadata.get('type', 'unknown').title()}")

                        # Context-specific information
                        if metadata.get("type") == "table":
                            print(f"   Table: {metadata.get('table_name', 'unknown')}")
                            print(
                                f"   Columns: {metadata.get('column_count', 'unknown')}"
                            )
                        elif metadata.get("type") == "column":
                            print(
                                f"   Table.Column: {metadata.get('table_name', 'unknown')}.{metadata.get('column_name', 'unknown')}"
                            )
                            print(
                                f"   Data Type: {metadata.get('column_type', 'unknown')}"
                            )
                        elif metadata.get("type") == "collection":
                            print(
                                f"   Collection: {metadata.get('collection_name', 'unknown')}"
                            )
                            print(
                                f"   Documents: {metadata.get('document_count', 'unknown')}"
                            )
                        elif metadata.get("type") == "relationship":
                            print(f"   From: {metadata.get('from_table', 'unknown')}")
                            print(f"   To: {metadata.get('to_table', 'unknown')}")

                        # Show content preview
                        content_preview = result["content"][:300]
                        if len(result["content"]) > 300:
                            content_preview += "..."
                        print(f"   Content: {content_preview}")
            else:
                print("❌ No relevant results found. Try rephrasing your question.")
                print("\n💡 Tips:")
                print("   • Be specific about what you're looking for")
                print(
                    "   • Use keywords like 'table', 'column', 'field', 'relationship'"
                )
                print("   • Ask about data types, constraints, or business purpose")

        except KeyboardInterrupt:
            print("\n❌ Question cancelled")

    def view_rag_overview(self):
        """View enhanced RAG system overview"""
        print("\n📊 RAG System Overview:")
        print("=" * 50)

        overview = self.connector.get_rag_overview()

        print(f"📈 Statistics:")
        print(f"   • Total Documents: {overview['total_documents']}")
        print(f"   • Databases: {len(overview['databases'])}")

        if overview["document_types"]:
            print(f"\n📄 Document Types:")
            for doc_type, count in overview["document_types"].items():
                print(f"   • {doc_type.title()}: {count}")

        if overview["databases"]:
            print(f"\n🗄️ Databases in RAG System:")
            for db_name, db_info in overview["databases"].items():
                print(f"\n   📁 {db_name} ({db_info['type']})")
                print(f"      Documents: {db_info['document_count']}")

                if db_info["tables"]:
                    print(
                        f"      Tables ({len(db_info['tables'])}): {', '.join(db_info['tables'][:5])}"
                    )
                    if len(db_info["tables"]) > 5:
                        print(f"         ... and {len(db_info['tables']) - 5} more")

                if db_info["collections"]:
                    print(
                        f"      Collections ({len(db_info['collections'])}): {', '.join(db_info['collections'][:5])}"
                    )
                    if len(db_info["collections"]) > 5:
                        print(
                            f"         ... and {len(db_info['collections']) - 5} more"
                        )

    def test_schema_search(self):
        """Test schema search with improved examples"""
        print("\n🧪 Testing Enhanced Schema Search:")
        print("-" * 40)

        test_queries = [
            # Metadata queries (will get direct answers)
            "How many tables are there?",
            "What databases do we have?",
            "Give me an overview of the schema",
            # Semantic queries (will use embeddings)
            "Show me all student related tables",
            "Find columns that store email addresses",
            "What tables have primary keys?",
            "Show me foreign key relationships",
            "Find fields that store dates or timestamps",
            "What collections are in MongoDB?",
            "Show me all ID columns",
        ]

        print("Available test queries:")
        for i, query in enumerate(test_queries, 1):
            query_type = "📊 Metadata" if i <= 3 else "🔍 Semantic"
            print(f"{i:2d}. {query_type}: {query}")

        try:
            choice = int(input("\nSelect a test query (1-11) or 0 for custom: "))

            if choice == 0:
                query = input("Enter custom query: ").strip()
            elif 1 <= choice <= len(test_queries):
                query = test_queries[choice - 1]
            else:
                print("❌ Invalid selection")
                return

            if query:
                print(f"\n🔄 Testing: '{query}'")
                print("-" * 40)

                results = self.connector.rag.search_schema(query, n_results=3)

                if results:
                    if results[0]["metadata"].get("type") == "metadata_answer":
                        print(f"🎯 Direct Answer: {results[0]['content']}")
                    else:
                        print(f"🎯 Found {len(results)} semantic matches:")
                        for i, result in enumerate(results, 1):
                            print(
                                f"{i}. {result['metadata'].get('type', 'unknown').title()} - "
                                f"Relevance: {result['relevance']} - "
                                f"Score: {result['similarity_score']:.3f}"
                            )
                            print(f"   Preview: {result['content'][:100]}...")
                else:
                    print("❌ No results found")

        except (ValueError, KeyboardInterrupt):
            print("❌ Invalid input or operation cancelled")

    def reset_rag_collection(self):
        """Reset RAG collection with confirmation"""
        print("\n⚠️ Reset RAG Collection:")
        print("This will delete all stored schema information!")

        confirm = input("Are you sure? Type 'yes' to confirm: ").strip().lower()

        if confirm == "yes":
            success = self.connector.rag.reset_collection()
            if success:
                print("✅ RAG collection reset successfully")
            else:
                print("❌ Failed to reset RAG collection")
        else:
            print("❌ Reset cancelled")

    async def ask_database_question(self):
        """Ask questions about schema or data using natural language"""
        print("\n🧠 Ask Questions About Your Database:")
        print("=" * 50)

        overview = self.connector.get_rag_overview()
        if overview["total_documents"] == 0:
            print(
                "❌ No schemas stored in RAG system. Please discover and store schemas first."
            )
            return

        # First check if we have any active connections
        if not self.current_connections:
            print("❌ No active database connections. Please connect first.")
            return

        print(f"📊 System Status:")
        print(f"   • {overview['total_documents']} schema documents indexed")
        print(
            f"   • {len(overview['databases'])} database(s): {', '.join(overview['databases'].keys())}"
        )
        print(f"   • {len(self.current_connections)} active connection(s)")
        print()

        print("💡 Example Questions:")
        print("📋 Schema Questions:")
        print("   • How many tables are there?")
        print("   • Show me the structure of the users table")
        print("   • What foreign keys exist?")
        print("\n📊 Data Questions:")
        print("   • Show me the top 5 customers by orders")
        print("   • What's the average order value?")
        print("   • Find all orders from last month")
        print()

        try:
            query = input("🤔 Your question: ").strip()
            if not query:
                print("❌ Question cannot be empty")
                return

            # Get database context
            if len(overview["databases"]) > 1:
                print(
                    f"\nAvailable databases: {', '.join(overview['databases'].keys())}"
                )
                database = input("Which database? ").strip()
                if not database in overview["databases"]:
                    print("❌ Invalid database")
                    return
            else:
                database = next(iter(overview["databases"]))

            print(f"\n🔄 Analyzing question...")

            # Get schema context for the database
            schema_context = self.connector.get_schema_context(database)

            # Analyze query with Gemini
            analysis = await self.gemini.analyze_query(query, schema_context)

            if analysis.get("type") == "error":
                print(f"❌ Error: {analysis['message']}")
                return

            if analysis["type"] == "schema":
                # Handle schema question with RAG
                await self._handle_schema_question(query, database)
            else:
                # Handle data question with Gemini SQL generation
                await self._handle_data_question(query, database, schema_context)

        except KeyboardInterrupt:
            print("\n❌ Question cancelled")
        except Exception as e:
            print(f"❌ Error: {e}")

    async def _handle_schema_question(self, query: str, database: str):
        """Handle schema-related questions using RAG"""
        results = self.connector.rag.search_schema(
            query=query, n_results=5, database_filter=database
        )

        if not results:
            print("❌ No relevant schema information found")
            return

        if results[0]["metadata"].get("type") == "metadata_answer":
            print(f"\n💡 Answer:")
            print(f"   {results[0]['content']}")

            if "details" in results[0]:
                details = results[0]["details"]
                if "tables" in details:
                    print(f"\n📋 Tables: {', '.join(details['tables'])}")
                if "breakdown" in details:
                    print(f"\n📊 Breakdown by database:")
                    for db, count in details["breakdown"].items():
                        print(f"   • {db}: {count} tables")
        else:
            print(f"\n🎯 Found {len(results)} relevant results:")
            for i, result in enumerate(results, 1):
                self._display_schema_result(i, result)

    async def _handle_data_question(
        self, query: str, database: str, schema_context: str
    ):
        """Handle data-related questions using Gemini with better error handling"""
        print("\n🔄 Generating SQL query...")

        # Find the database connection
        db_config = None
        db_type = None

        # Get the database type from RAG overview
        overview = self.connector.get_rag_overview()
        if database in overview["databases"]:
            db_type_str = overview["databases"][database][
                "type"
            ].lower()  # Convert to lowercase

            # Map the database type string to enum
            db_type_mapping = {
                "mysql": DatabaseType.MYSQL,
                "postgresql": DatabaseType.POSTGRESQL,
                "postgres": DatabaseType.POSTGRESQL,  # Alternative name
                "mongodb": DatabaseType.MONGODB,
                "mongo": DatabaseType.MONGODB,  # Alternative name
            }

            if db_type_str in db_type_mapping:
                db_type = db_type_mapping[db_type_str]
            else:
                print(f"❌ Unsupported database type: {db_type_str}")
                return

            # Find the corresponding connection using the enum value
            if db_type.value in self.current_connections:
                db_config = self.current_connections[db_type.value]
            else:
                # Try to find any connection of this type (case-insensitive)
                for conn_key, conn_val in self.current_connections.items():
                    if conn_key.lower() == db_type.value.lower():
                        db_config = conn_val
                        break

        if not db_config or not db_type:
            print("❌ Database connection not found.")
            print(f"Available connections: {list(self.current_connections.keys())}")
            print(f"Target database: {database}")
            if database in overview["databases"]:
                print(
                    f"Database type from RAG: {overview['databases'][database]['type']}"
                )

            # Debug information to help troubleshoot
            print("\n🔍 Debug Information:")
            print(f"Looking for database: {database}")
            print(f"RAG databases: {list(overview['databases'].keys())}")
            print(f"Current connections: {list(self.current_connections.keys())}")
            return

        # Continue with the rest of the method (add the missing get_table_list method call)
        print("🔍 Checking available tables...")
        try:
            actual_tables = await self.get_table_list(db_type, db_config)
            if actual_tables:
                print(f"📋 Available tables: {', '.join(actual_tables)}")
                schema_context += (
                    f"\n\nActual tables in database: {', '.join(actual_tables)}"
                )
            else:
                print("⚠️ No tables found in database or unable to retrieve table list")
        except Exception as e:
            print(f"⚠️ Could not retrieve table list: {e}")

        # Generate SQL with Gemini
        sql_result = await self.gemini.generate_sql(
            query, schema_context, db_type.value
        )

        if sql_result.get("type") == "error":
            print(f"❌ Error generating SQL: {sql_result['message']}")
            return

        # Display generated SQL
        print("\n📝 Generated SQL:")
        print(f"   {sql_result['query']}")

        if sql_result.get("explanation"):
            print("\n💡 Explanation:")
            print(f"   {sql_result['explanation']}")

        if sql_result.get("warnings"):
            print("\n⚠️ Warnings:")
            for warning in sql_result["warnings"]:
                print(f"   • {warning}")

        # Ask for confirmation with options
        execute_choice = input(
            "\nOptions:\n1. Execute query\n2. Modify query\n3. Show tables first\n4. Cancel\nChoice (1-4): "
        ).strip()

        if execute_choice == "2":
            modified_query = input(
                f"\nModify SQL query:\nOriginal: {sql_result['query']}\nNew: "
            ).strip()
            if modified_query:
                sql_result["query"] = modified_query
                print(f"✅ Using modified query: {modified_query}")
            else:
                print("❌ No modification made, using original query")
        elif execute_choice == "3":
            try:
                # FIX: Use direct table listing method
                actual_tables = await self.get_table_list(db_type, db_config)

                if actual_tables:
                    print("\n📋 Available tables:")
                    for i, table_name in enumerate(actual_tables, 1):
                        print(f"   {i}. {table_name}")
                else:
                    print("   No tables found")

                if (
                    input("\nNow execute the original query? (yes/no): ").lower()
                    != "yes"
                ):
                    print("❌ Query cancelled")
                    return

            except Exception as show_error:
                print(f"   Error retrieving tables: {show_error}")
                return
        elif execute_choice != "1":
            print("❌ Query cancelled")
            return

        # Execute query
        print("\n🔄 Executing query...")
        try:
            results = await self.connector.execute_query(db_type, sql_result["query"])

            print("\n📊 Results:")
            if not results:
                print("   No results found")
                return

            print(f"   Found {len(results)} rows:")
            for i, row in enumerate(results[:10], 1):
                if isinstance(row, dict):
                    formatted_row = ", ".join([f"{k}: {v}" for k, v in row.items()])
                elif isinstance(row, (list, tuple)):
                    formatted_row = ", ".join([str(val) for val in row])
                else:
                    formatted_row = str(row)
                print(f"   {i:2d}. {formatted_row}")

            if len(results) > 10:
                print(f"   ... and {len(results) - 10} more rows")

            print("\n🔄 Analyzing results...")
            explanation = await self.gemini.explain_data_results(
                query, results[:5], schema_context
            )
            print("\n💡 Analysis:")
            print(f"   {explanation}")

        except Exception as e:
            error_msg = str(e)
            print(f"❌ Error executing query: {error_msg}")

            if "doesn't exist" in error_msg:
                print("\n💡 Suggestions:")
                print("   • The table name might be incorrect")
                print("   • Try asking 'What tables are available?' first")

                show_tables = input(
                    "\nWould you like to see available tables? (yes/no): "
                ).lower()
                if show_tables == "yes":
                    try:
                        tables_result = await self.connector.execute_query(
                            db_type, "SHOW TABLES"
                        )
                        if tables_result:
                            print("\n📋 Available tables:")
                            for i, table in enumerate(tables_result, 1):
                                table_name = (
                                    table[0]
                                    if isinstance(table, (list, tuple))
                                    else str(table)
                                )
                                print(f"   {i}. {table_name}")
                        else:
                            print("   No tables found")
                    except Exception as show_error:
                        print(f"   Error retrieving tables: {show_error}")

    def _display_schema_result(self, index: int, result: Dict[str, Any]):
        """Display a single schema search result with formatting"""
        print(f"\n📋 Result {index} ({result['relevance'].title()} Relevance):")
        print(f"   Database: {result['metadata'].get('database_name', 'unknown')}")
        print(f"   Type: {result['metadata'].get('type', 'unknown').title()}")
        print(f"   Similarity: {result['similarity_score']:.3f}")

        # Display type-specific information
        metadata = result["metadata"]
        doc_type = metadata.get("type", "unknown")

        if doc_type == "table":
            print(f"   Table: {metadata.get('table_name', 'unknown')}")
            print(f"   Column Count: {metadata.get('column_count', 'unknown')}")
            if metadata.get("has_primary_key"):
                print(f"   Primary Keys: {metadata.get('primary_keys', '')}")

        elif doc_type == "column":
            print(
                f"   Table.Column: {metadata.get('table_name', 'unknown')}.{metadata.get('column_name', 'unknown')}"
            )
            print(f"   Data Type: {metadata.get('column_type', 'unknown')}")
            print(f"   Nullable: {'Yes' if metadata.get('is_nullable') else 'No'}")
            if metadata.get("is_primary_key"):
                print("   Primary Key: Yes")

        elif doc_type == "collection":
            print(f"   Collection: {metadata.get('collection_name', 'unknown')}")
            print(f"   Document Count: {metadata.get('document_count', 'unknown')}")

        elif doc_type == "relationship":
            print(
                f"   From: {metadata.get('from_table', 'unknown')}.{metadata.get('from_column', 'unknown')}"
            )
            print(
                f"   To: {metadata.get('to_table', 'unknown')}.{metadata.get('to_column', 'unknown')}"
            )

        # Display content preview
        content = result["content"]
        preview = content[:300] + "..." if len(content) > 300 else content
        print(f"   Content: {preview}")

    async def get_table_list(
        self, db_type: DatabaseType, config: DatabaseConfig
    ) -> List[str]:
        """Get actual list of tables from the database - with debug info"""
        try:
            if db_type == DatabaseType.MYSQL:
                query = "SHOW TABLES"
            elif db_type == DatabaseType.POSTGRESQL:
                query = "SELECT tablename FROM pg_tables WHERE schemaname = 'public'"
            else:
                return []

            print(f"🔍 Debug: Executing '{query}' on {db_type.value}")

            # Try using execute_query with proper connection setup
            try:
                # Store current connection for this database type
                original_connection = self.connector.current_connections.get(
                    db_type.value
                )

                # Set up the connection for this query
                self.connector.current_connections[db_type.value] = config

                # Execute the query
                results = await self.connector.execute_query(db_type, query)

                print(f"🔍 Debug: Raw results: {results}")
                print(f"🔍 Debug: Results type: {type(results)}")
                if results:
                    print(f"🔍 Debug: Number of results: {len(results)}")
                    for i, row in enumerate(results):
                        print(f"🔍 Debug: Row {i}: {row} (type: {type(row)})")

                # Restore original connection
                if original_connection:
                    self.connector.current_connections[db_type.value] = (
                        original_connection
                    )
                else:
                    self.connector.current_connections.pop(db_type.value, None)

            except AttributeError as ae:
                print(f"🔍 Debug: AttributeError - using direct connection: {ae}")
                # Option 2: If execute_query doesn't work, try direct database connection
                if db_type == DatabaseType.MYSQL:
                    import aiomysql

                    conn = await aiomysql.connect(
                        host=config.host,
                        port=config.port,
                        user=config.username,
                        password=config.password,
                        db=config.database,
                    )
                    async with conn.cursor() as cursor:
                        await cursor.execute(query)
                        results = await cursor.fetchall()
                        print(f"🔍 Debug: Direct connection results: {results}")
                    await conn.ensure_closed()
                else:
                    return []

            # Extract table names from results - ENHANCED PROCESSING
            table_names = []
            if results:
                print(f"🔍 Debug: Processing {len(results)} results")

                for i, row in enumerate(results):
                    print(f"🔍 Debug: Processing row {i}: {row}")

                    if isinstance(row, (list, tuple)):
                        table_name = str(row[0])
                        print(f"🔍 Debug: Extracted from tuple/list: '{table_name}'")
                    elif isinstance(row, dict):
                        # Handle dictionary results
                        table_name = str(list(row.values())[0])
                        print(f"🔍 Debug: Extracted from dict: '{table_name}'")
                    else:
                        table_name = str(row)
                        print(f"🔍 Debug: Extracted as string: '{table_name}'")

                    table_names.append(table_name)

            print(f"🔍 Debug: Final table list: {table_names}")
            return table_names

        except Exception as e:
            print(f"Error getting table list: {e}")
            import traceback

            traceback.print_exc()
            return []

    # Update the menu handler
    async def run(self):
        """Run the enhanced CLI application"""
        self.display_welcome()

        try:
            while True:
                self.display_menu()

                try:
                    choice = input("Enter your choice (1-11): ").strip()

                    if choice == "1":
                        await self.connect_database(DatabaseType.MYSQL)
                    elif choice == "2":
                        await self.connect_database(DatabaseType.POSTGRESQL)
                    elif choice == "3":
                        await self.connect_database(DatabaseType.MONGODB)
                    elif choice == "4":
                        self.view_connections()
                    elif choice == "5":
                        await self.discover_and_store_schema()
                    elif choice == "6":
                        self.view_schema_summary()
                    elif choice == "7":
                        await self.ask_database_question()  # Updated to new method
                    elif choice == "8":
                        self.view_rag_overview()
                    elif choice == "9":
                        self.test_schema_search()
                    elif choice == "10":
                        self.reset_rag_collection()
                    elif choice == "11":
                        print("\n👋 Closing all connections...")
                        await self.connector.close_all_connections()
                        print("✅ All connections closed. Goodbye!")
                        break
                    else:
                        print("❌ Invalid choice. Please enter 1-11.")

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
    cli = EnhancedDatabaseCLI()
    await cli.run()


if __name__ == "__main__":
    asyncio.run(main())
