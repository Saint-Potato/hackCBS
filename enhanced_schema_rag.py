import chromadb
from chromadb.config import Settings
import uuid
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import json
import logging
from sentence_transformers import SentenceTransformer
import numpy as np
from database_connector import DatabaseType, DatabaseConnector
import re

logger = logging.getLogger(__name__)

@dataclass
class SchemaDocument:
    """Represents a schema document for RAG storage"""
    id: str
    content: str
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None

class EnhancedSchemaRAG:
    """Enhanced RAG system for database schema using ChromaDB with smart query handling"""
    
    def __init__(self, persist_directory: str = "./chroma_db", model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize EnhancedSchemaRAG with ChromaDB
        
        Args:
            persist_directory: Directory to persist ChromaDB data
            model_name: SentenceTransformer model for embeddings
        """
        self.persist_directory = persist_directory
        self.model_name = model_name
        
        # Initialize SentenceTransformer for embeddings
        logger.info(f"Loading embedding model: {model_name}")
        self.embedding_model = SentenceTransformer(model_name)
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Create or get collection for schemas
        self.collection = self.client.get_or_create_collection(
            name="database_schemas",
            metadata={"description": "Database schema information for RAG"},
            embedding_function=None  # We'll handle embeddings manually
        )
        
        logger.info(f"ChromaDB initialized with collection: {self.collection.name}")
    
    def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text using SentenceTransformer"""
        try:
            embedding = self.embedding_model.encode(text, convert_to_tensor=False)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return []
    
    def _sanitize_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize metadata to ensure ChromaDB compatibility"""
        sanitized = {}
        
        for key, value in metadata.items():
            if value is None:
                sanitized[key] = ""
            elif isinstance(value, (str, int, float, bool)):
                sanitized[key] = value
            elif isinstance(value, list):
                # Convert lists to comma-separated strings
                sanitized[key] = ",".join(str(v) for v in value) if value else ""
            elif isinstance(value, dict):
                # Convert dicts to JSON strings
                sanitized[key] = json.dumps(value)
            else:
                # Convert other types to strings
                sanitized[key] = str(value)
        
        return sanitized
    
    def _is_metadata_query(self, query: str) -> bool:
        """Check if query is asking for metadata/statistics rather than content search"""
        metadata_patterns = [
            r'how many.*table',
            r'how many.*column',
            r'how many.*database',
            r'count.*table',
            r'count.*column',
            r'list.*table',
            r'list.*column',
            r'show.*all.*table',
            r'what.*table.*exist',
            r'give me.*overview',
            r'summary',
            r'statistics'
        ]
        
        query_lower = query.lower()
        return any(re.search(pattern, query_lower) for pattern in metadata_patterns)
    
    def _answer_metadata_query(self, query: str, database_filter: Optional[str] = None) -> Dict[str, Any]:
        """Answer metadata queries directly using stored information"""
        overview = self.get_database_overview()
        query_lower = query.lower()
        
        response = {
            "type": "metadata_answer",
            "query": query,
            "answer": "",
            "details": {}
        }
        
        # Filter by database if specified
        if database_filter and database_filter in overview["databases"]:
            db_info = overview["databases"][database_filter]
            
            if "table" in query_lower:
                table_count = len(db_info["tables"])
                collection_count = len(db_info["collections"])
                
                if table_count > 0:
                    response["answer"] = f"The '{database_filter}' database has {table_count} table{'s' if table_count != 1 else ''}."
                    response["details"]["tables"] = db_info["tables"]
                elif collection_count > 0:
                    response["answer"] = f"The '{database_filter}' database has {collection_count} collection{'s' if collection_count != 1 else ''}."
                    response["details"]["collections"] = db_info["collections"]
                else:
                    response["answer"] = f"The '{database_filter}' database has no tables or collections stored in the RAG system."
            
            elif "column" in query_lower:
                # Count columns by looking at document types
                column_count = sum(1 for doc_type, count in overview["document_types"].items() if doc_type == "column")
                response["answer"] = f"The '{database_filter}' database has approximately {column_count} columns across all tables."
        
        else:
            # Answer for all databases
            total_dbs = len(overview["databases"])
            total_tables = sum(len(db["tables"]) for db in overview["databases"].values())
            total_collections = sum(len(db["collections"]) for db in overview["databases"].values())
            
            if "table" in query_lower:
                if total_tables > 0:
                    response["answer"] = f"There are {total_tables} table{'s' if total_tables != 1 else ''} across {total_dbs} database{'s' if total_dbs != 1 else ''}."
                    response["details"]["breakdown"] = {db_name: len(db_info["tables"]) for db_name, db_info in overview["databases"].items()}
                if total_collections > 0:
                    response["answer"] += f" Additionally, there are {total_collections} MongoDB collection{'s' if total_collections != 1 else ''}."
                    response["details"]["collections_breakdown"] = {db_name: len(db_info["collections"]) for db_name, db_info in overview["databases"].items()}
            
            elif "database" in query_lower:
                response["answer"] = f"There are {total_dbs} database{'s' if total_dbs != 1 else ''} stored in the RAG system: {', '.join(overview['databases'].keys())}"
                response["details"]["databases"] = list(overview["databases"].keys())
            
            elif "overview" in query_lower or "summary" in query_lower:
                response["answer"] = f"RAG System Overview: {total_dbs} database{'s' if total_dbs != 1 else ''}, {total_tables + total_collections} table{'s' if total_tables + total_collections != 1 else ''}/collection{'s' if total_tables + total_collections != 1 else ''}, {overview['total_documents']} total schema documents."
                response["details"] = overview
        
        return response
    
    def _create_table_documents(self, schema: Dict[str, Any], db_type: DatabaseType, db_config: Dict[str, str]) -> List[SchemaDocument]:
        """Create documents from table/collection schema"""
        documents = []
        
        if db_type in [DatabaseType.MYSQL, DatabaseType.POSTGRESQL]:
            tables = schema.get("tables", {})
            relationships = schema.get("relationships", [])
            
            # Create document for each table
            for table_name, table_info in tables.items():
                # Main table document
                table_content = self._format_table_content(table_name, table_info, db_type)
                
                doc = SchemaDocument(
                    id=f"{db_config['database']}_{db_type.value}_{table_name}",
                    content=table_content,
                    metadata=self._sanitize_metadata({
                        "type": "table",
                        "database_type": db_type.value,
                        "database_name": db_config["database"],
                        "host": db_config["host"],
                        "table_name": table_name,
                        "column_count": len(table_info.get("columns", [])),
                        "has_primary_key": len(table_info.get("primary_keys", [])) > 0,
                        "primary_keys": table_info.get("primary_keys", [])
                    })
                )
                documents.append(doc)
                
                # Create documents for individual columns
                for column in table_info.get("columns", []):
                    column_content = self._format_column_content(table_name, column, db_type)
                    
                    col_doc = SchemaDocument(
                        id=f"{db_config['database']}_{db_type.value}_{table_name}_{column['name']}",
                        content=column_content,
                        metadata=self._sanitize_metadata({
                            "type": "column",
                            "database_type": db_type.value,
                            "database_name": db_config["database"],
                            "host": db_config["host"],
                            "table_name": table_name,
                            "column_name": column["name"],
                            "column_type": column.get("type", "unknown"),
                            "is_nullable": column.get("null", False),
                            "is_primary_key": column["name"] in table_info.get("primary_keys", [])
                        })
                    )
                    documents.append(col_doc)
            
            # Create relationship documents
            for i, rel in enumerate(relationships):
                rel_content = self._format_relationship_content(rel, db_type)
                
                rel_doc = SchemaDocument(
                    id=f"{db_config['database']}_{db_type.value}_relationship_{i}",
                    content=rel_content,
                    metadata=self._sanitize_metadata({
                        "type": "relationship",
                        "database_type": db_type.value,
                        "database_name": db_config["database"],
                        "host": db_config["host"],
                        "from_table": rel["from_table"],
                        "from_column": rel["from_column"],
                        "to_table": rel["to_table"],
                        "to_column": rel["to_column"]
                    })
                )
                documents.append(rel_doc)
        
        elif db_type == DatabaseType.MONGODB:
            collections = schema.get("collections", {})
            
            for collection_name, collection_info in collections.items():
                # Main collection document
                collection_content = self._format_collection_content(collection_name, collection_info)
                
                doc = SchemaDocument(
                    id=f"{db_config['database']}_{db_type.value}_{collection_name}",
                    content=collection_content,
                    metadata=self._sanitize_metadata({
                        "type": "collection",
                        "database_type": db_type.value,
                        "database_name": db_config["database"],
                        "host": db_config["host"],
                        "collection_name": collection_name,
                        "document_count": collection_info.get("document_count", 0),
                        "field_count": len(collection_info.get("fields", {}))
                    })
                )
                documents.append(doc)
                
                # Create documents for fields
                for field_name, field_info in collection_info.get("fields", {}).items():
                    field_content = self._format_field_content(collection_name, field_name, field_info)
                    
                    field_doc = SchemaDocument(
                        id=f"{db_config['database']}_{db_type.value}_{collection_name}_{field_name.replace('.', '_')}",
                        content=field_content,
                        metadata=self._sanitize_metadata({
                            "type": "field",
                            "database_type": db_type.value,
                            "database_name": db_config["database"],
                            "host": db_config["host"],
                            "collection_name": collection_name,
                            "field_name": field_name,
                            "field_types": field_info.get("types", []),
                            "field_count": field_info.get("count", 0),
                            "null_count": field_info.get("null_count", 0)
                        })
                    )
                    documents.append(field_doc)
        
        return documents
    
    def _format_table_content(self, table_name: str, table_info: Dict, db_type: DatabaseType) -> str:
        """Format table information into searchable text with better keywords"""
        content = f"Table: {table_name} in {db_type.value} database\n"
        content += f"Description: This is a {table_name} table with {len(table_info.get('columns', []))} columns.\n"
        
        # Add searchable keywords
        content += f"Keywords: table, {table_name}, database table, data storage, {db_type.value}\n"
        
        # Add column information
        columns = table_info.get("columns", [])
        if columns:
            content += "Columns and fields:\n"
            for col in columns:
                content += f"- {col['name']} ({col.get('type', 'unknown')})"
                if not col.get("null", True):
                    content += " NOT NULL"
                if col["name"] in table_info.get("primary_keys", []):
                    content += " PRIMARY KEY"
                content += "\n"
        
        # Add primary key information
        primary_keys = table_info.get("primary_keys", [])
        if primary_keys:
            content += f"Primary Keys: {', '.join(primary_keys)}\n"
        
        # Add business context hints
        content += f"Business Context: The {table_name} table likely contains information about {self._infer_table_purpose(table_name)}.\n"
        
        # Add common search terms
        content += f"Related terms: {table_name} data, {table_name} information, {table_name} records\n"
        
        return content
    
    def _format_column_content(self, table_name: str, column: Dict, db_type: DatabaseType) -> str:
        """Format column information into searchable text with better keywords"""
        content = f"Column: {column['name']} in table {table_name}\n"
        content += f"Data Type: {column.get('type', 'unknown')}\n"
        content += f"Nullable: {'Yes' if column.get('null', True) else 'No'}\n"
        
        # Add searchable keywords
        content += f"Keywords: column, field, {column['name']}, {table_name}, data field\n"
        
        if column.get('default'):
            content += f"Default Value: {column['default']}\n"
        
        # Add business context
        content += f"Business Context: The {column['name']} field likely represents {self._infer_column_purpose(column['name'])}.\n"
        
        return content
    
    def _format_relationship_content(self, relationship: Dict, db_type: DatabaseType) -> str:
        """Format relationship information into searchable text"""
        content = f"Foreign Key Relationship in {db_type.value} database\n"
        content += f"From: {relationship['from_table']}.{relationship['from_column']}\n"
        content += f"To: {relationship['to_table']}.{relationship['to_column']}\n"
        content += f"Keywords: relationship, foreign key, connection, join, link\n"
        content += f"This relationship connects {relationship['from_table']} to {relationship['to_table']} "
        content += f"through the {relationship['from_column']} and {relationship['to_column']} columns.\n"
        
        return content
    
    def _format_collection_content(self, collection_name: str, collection_info: Dict) -> str:
        """Format MongoDB collection information into searchable text"""
        content = f"Collection: {collection_name} in MongoDB database\n"
        content += f"Document Count: {collection_info.get('document_count', 0)}\n"
        content += f"Fields: {len(collection_info.get('fields', {}))}\n"
        content += f"Keywords: collection, {collection_name}, MongoDB, documents, NoSQL\n"
        
        # Add field summary
        fields = collection_info.get("fields", {})
        if fields:
            content += "Field Summary:\n"
            for field_name, field_info in list(fields.items())[:10]:
                types = ', '.join(field_info.get('types', []))
                content += f"- {field_name}: {types}\n"
        
        # Add business context
        content += f"Business Context: The {collection_name} collection likely stores {self._infer_collection_purpose(collection_name)}.\n"
        
        return content
    
    def _format_field_content(self, collection_name: str, field_name: str, field_info: Dict) -> str:
        """Format MongoDB field information into searchable text"""
        content = f"Field: {field_name} in collection {collection_name}\n"
        types = field_info.get('types', [])
        content += f"Data Types: {', '.join(types)}\n"
        content += f"Keywords: field, {field_name}, {collection_name}, MongoDB field\n"
        content += f"Occurrences: {field_info.get('count', 0)} documents\n"
        
        null_count = field_info.get('null_count', 0)
        total_count = field_info.get('count', 1)
        null_percentage = (null_count / total_count) * 100 if total_count > 0 else 0
        content += f"Null Values: {null_count} ({null_percentage:.1f}%)\n"
        
        # Add business context
        content += f"Business Context: The {field_name} field likely represents {self._infer_field_purpose(field_name)}.\n"
        
        return content
    
    def _infer_table_purpose(self, table_name: str) -> str:
        """Infer business purpose of table from name"""
        table_lower = table_name.lower()
        
        purpose_mapping = {
            'user': 'user accounts and profiles',
            'customer': 'customer information and details',
            'order': 'purchase orders and transactions',
            'product': 'product catalog and inventory',
            'invoice': 'billing and invoice records',
            'payment': 'payment transactions and methods',
            'employee': 'staff and employee records',
            'category': 'classification and categorization data',
            'log': 'system logs and audit trails',
            'session': 'user sessions and authentication',
            'address': 'location and address information',
            'review': 'product or service reviews',
            'cart': 'shopping cart and basket data',
            'student': 'student information and academic records',
            'course': 'course information and curriculum data',
            'teacher': 'teacher profiles and assignments',
            'grade': 'academic grades and assessments',
            'class': 'class schedules and information',
            'school': 'school or institution data'
        }
        
        for key, purpose in purpose_mapping.items():
            if key in table_lower:
                return purpose
        
        return f"data related to {table_name}"
    
    def _infer_column_purpose(self, column_name: str) -> str:
        """Infer business purpose of column from name"""
        column_lower = column_name.lower()
        
        purpose_mapping = {
            'id': 'unique identifier',
            'name': 'name or title',
            'email': 'email address',
            'password': 'authentication credentials',
            'phone': 'phone number',
            'address': 'physical address',
            'date': 'date information',
            'time': 'time information',
            'price': 'monetary amount',
            'amount': 'quantity or monetary value',
            'status': 'current state or status',
            'created': 'creation timestamp',
            'updated': 'last modification timestamp',
            'deleted': 'deletion timestamp',
            'active': 'active/inactive status',
            'description': 'detailed description',
            'title': 'title or heading',
            'age': 'age information',
            'grade': 'grade or score',
            'level': 'level or rank',
            'department': 'department or division'
        }
        
        for key, purpose in purpose_mapping.items():
            if key in column_lower:
                return purpose
        
        return f"information about {column_name}"
    
    def _infer_collection_purpose(self, collection_name: str) -> str:
        """Infer business purpose of MongoDB collection from name"""
        return self._infer_table_purpose(collection_name)
    
    def _infer_field_purpose(self, field_name: str) -> str:
        """Infer business purpose of MongoDB field from name"""
        return self._infer_column_purpose(field_name)
    
    async def store_schema(self, schema: Dict[str, Any], db_type: DatabaseType, db_config: Dict[str, str]) -> bool:
        """Store database schema in ChromaDB"""
        try:
            logger.info(f"Storing schema for {db_type.value} database: {db_config['database']}")
            
            # Create documents from schema
            documents = self._create_table_documents(schema, db_type, db_config)
            
            if not documents:
                logger.warning("No documents created from schema")
                return False
            
            # Generate embeddings and prepare for storage
            ids = []
            contents = []
            embeddings = []
            metadatas = []
            
            for doc in documents:
                # Generate embedding
                embedding = self._generate_embedding(doc.content)
                if not embedding:
                    logger.warning(f"Failed to generate embedding for document {doc.id}")
                    continue
                
                ids.append(doc.id)
                contents.append(doc.content)
                embeddings.append(embedding)
                metadatas.append(doc.metadata)
            
            # Store in ChromaDB (upsert to handle updates)
            if ids:
                self.collection.upsert(
                    ids=ids,
                    documents=contents,
                    embeddings=embeddings,
                    metadatas=metadatas
                )
                
                logger.info(f"Successfully stored {len(ids)} schema documents in ChromaDB")
                return True
            else:
                logger.error("No valid documents to store")
                return False
                
        except Exception as e:
            logger.error(f"Error storing schema in ChromaDB: {e}")
            return False
    
    def search_schema(self, query: str, n_results: int = 5, database_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """Enhanced search that handles both metadata and semantic queries"""
        try:
            # Check if this is a metadata query
            if self._is_metadata_query(query):
                metadata_response = self._answer_metadata_query(query, database_filter)
                return [{
                    "content": metadata_response["answer"],
                    "metadata": {
                        "type": "metadata_answer",
                        "query_type": "direct_answer",
                        "database_name": database_filter or "all"
                    },
                    "similarity_score": 1.0,
                    "relevance": "direct_answer",
                    "details": metadata_response.get("details", {})
                }]
            
            # Generate embedding for semantic search
            query_embedding = self._generate_embedding(query)
            if not query_embedding:
                logger.error("Failed to generate embedding for query")
                return []
            
            # Prepare filter
            where_filter = {}
            if database_filter:
                where_filter["database_name"] = database_filter
            
            # Search in ChromaDB
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where_filter if where_filter else None,
                include=["documents", "metadatas", "distances"]
            )
            
            # Format results with corrected similarity scores
            formatted_results = []
            if results["documents"] and results["documents"][0]:
                for i in range(len(results["documents"][0])):
                    distance = results["distances"][0][i]
                    # Ensure similarity is between 0 and 1, with higher values being better
                    similarity_score = max(0.0, 1.0 - distance) if distance >= 0 else abs(distance)
                    
                    # Determine relevance based on similarity
                    if similarity_score > 0.7:
                        relevance = "high"
                    elif similarity_score > 0.4:
                        relevance = "medium"
                    else:
                        relevance = "low"
                    
                    formatted_results.append({
                        "content": results["documents"][0][i],
                        "metadata": results["metadatas"][0][i],
                        "similarity_score": similarity_score,
                        "relevance": relevance
                    })
            
            logger.info(f"Found {len(formatted_results)} relevant schema documents for query: {query}")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error searching schema: {e}")
            return []
    
    def get_database_overview(self) -> Dict[str, Any]:
        """Get overview of stored database schemas"""
        try:
            # Get all documents
            results = self.collection.get(
                include=["metadatas"]
            )
            
            overview = {
                "total_documents": len(results["ids"]) if results["ids"] else 0,
                "databases": {},
                "document_types": {}
            }
            
            if results["metadatas"]:
                for metadata in results["metadatas"]:
                    db_name = metadata.get("database_name", "unknown")
                    db_type = metadata.get("database_type", "unknown")
                    doc_type = metadata.get("type", "unknown")
                    
                    # Count by database
                    if db_name not in overview["databases"]:
                        overview["databases"][db_name] = {
                            "type": db_type,
                            "document_count": 0,
                            "tables": set(),
                            "collections": set()
                        }
                    overview["databases"][db_name]["document_count"] += 1
                    
                    # Track tables/collections
                    if "table_name" in metadata:
                        overview["databases"][db_name]["tables"].add(metadata["table_name"])
                    if "collection_name" in metadata:
                        overview["databases"][db_name]["collections"].add(metadata["collection_name"])
                    
                    # Count by document type
                    overview["document_types"][doc_type] = overview["document_types"].get(doc_type, 0) + 1
                
                # Convert sets to lists for JSON serialization
                for db_info in overview["databases"].values():
                    db_info["tables"] = list(db_info["tables"])
                    db_info["collections"] = list(db_info["collections"])
            
            return overview
            
        except Exception as e:
            logger.error(f"Error getting database overview: {e}")
            return {"total_documents": 0, "databases": {}, "document_types": {}}
    
    def delete_database_schema(self, database_name: str) -> bool:
        """Delete all schema documents for a specific database"""
        try:
            # Get all documents for the database
            results = self.collection.get(
                where={"database_name": database_name},
                include=["ids"]
            )
            
            if results["ids"]:
                # Delete documents
                self.collection.delete(ids=results["ids"])
                logger.info(f"Deleted {len(results['ids'])} schema documents for database: {database_name}")
                return True
            else:
                logger.info(f"No schema documents found for database: {database_name}")
                return True
                
        except Exception as e:
            logger.error(f"Error deleting schema for database {database_name}: {e}")
            return False
    
    def reset_collection(self) -> bool:
        """Reset the entire schema collection"""
        try:
            self.client.delete_collection("database_schemas")
            self.collection = self.client.get_or_create_collection(
                name="database_schemas",
                metadata={"description": "Database schema information for RAG"},
                embedding_function=None
            )
            logger.info("Schema collection reset successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error resetting collection: {e}")
            return False

# Update the DatabaseConnectorWithRAG to use enhanced version
class EnhancedDatabaseConnectorWithRAG(DatabaseConnector):
    """Enhanced DatabaseConnector with improved RAG capabilities"""
    
    def __init__(self, persist_directory: str = "./chroma_db"):
        super().__init__()
        self.rag = EnhancedSchemaRAG(persist_directory)
        logger.info("Enhanced DatabaseConnector with RAG initialized")
    
    async def discover_and_store_schema(self, db_type: DatabaseType, config: dict) -> Dict[str, Any]:
        """Discover schema and store in RAG system"""
        schema = await self.discover_schema(db_type)
        
        if schema:
            db_config = {
                "database": config.get("database", "unknown"),
                "host": config.get("host", "unknown"),
                "port": str(config.get("port", "unknown"))
            }
            
            success = await self.rag.store_schema(schema, db_type, db_config)
            if success:
                logger.info(f"Schema successfully stored in RAG system for {db_type.value}")
            else:
                logger.error(f"Failed to store schema in RAG system for {db_type.value}")
        
        return schema
    
    def search_schema_context(self, query: str, database_filter: Optional[str] = None) -> str:
        """Search schema and return context for RAG"""
        results = self.rag.search_schema(query, n_results=5, database_filter=database_filter)
        
        if not results:
            return "No relevant schema information found."
        
        # Handle direct answers
        if results[0]["metadata"].get("type") == "metadata_answer":
            return results[0]["content"]
        
        # Handle semantic search results
        context = "Relevant Database Schema Information:\n\n"
        for i, result in enumerate(results, 1):
            context += f"{i}. {result['content']}\n"
            context += f"   Relevance: {result['relevance']}\n"
            context += f"   Database: {result['metadata'].get('database_name', 'unknown')}\n\n"
        
        return context
    
    def get_rag_overview(self) -> Dict[str, Any]:
        """Get overview of RAG system"""
        return self.rag.get_database_overview()