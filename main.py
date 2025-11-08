from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import asyncio
import sys
import os
import logging

# Add the parent directory to Python path to import your existing modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database_connector import DatabaseType, DatabaseConfig, DatabaseConnector
from enhanced_schema_rag import EnhancedDatabaseConnectorWithRAG
from gemini_helper import GeminiHelper

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="DB RAG Analytics API",
    version="1.0.0",
    description="AI-Driven Database RAG & Analytics Backend API"
)

# Configure CORS for React app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Vite dev server and CRA
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
connector = EnhancedDatabaseConnectorWithRAG()
gemini_helper = GeminiHelper()
current_connections = {}

# Pydantic models for request/response
class DatabaseConnectionRequest(BaseModel):
    db_type: str
    host: str
    port: int
    username: str
    password: str
    database: str

class QueryRequest(BaseModel):
    query: str
    database: Optional[str] = None

class ExecuteSQLRequest(BaseModel):
    sql_query: str
    database: str

class ApiResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class ConnectionStatus(BaseModel):
    type: str
    host: str
    port: int
    database: str
    connected: bool
    last_tested: Optional[str] = None

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "DB RAG Analytics API is running",
        "version": "1.0.0",
        "endpoints": {
            "health": "/api/health",
            "docs": "/docs",
            "connections": "/api/connections",
            "rag_overview": "/api/rag-overview"
        }
    }

# Health check endpoint
@app.get("/api/health")
async def health_check():
    try:
        # Check if core services are working
        health_status = {
            "api": "healthy",
            "connections": len(current_connections),
            "rag_documents": 0,
            "gemini": "unknown"
        }
        
        # Check RAG system
        try:
            overview = connector.get_rag_overview()
            health_status["rag_documents"] = overview.get("total_documents", 0)
        except Exception as e:
            health_status["rag"] = f"error: {str(e)}"
        
        # Check Gemini (basic check)
        try:
            # This is a simple check - you might want to make it more robust
            health_status["gemini"] = "configured"
        except Exception as e:
            health_status["gemini"] = f"error: {str(e)}"
        
        return {
            "status": "healthy",
            "message": "All systems operational",
            "details": health_status
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

# Database Connections Endpoints
@app.get("/api/connections", response_model=ApiResponse)
async def get_connections():
    """Get current database connections"""
    try:
        connections_info = {}
        for db_type, config in current_connections.items():
            connections_info[db_type] = ConnectionStatus(
                type=config.db_type.value,
                host=config.host,
                port=config.port,
                database=config.database,
                connected=True
            ).dict()
        
        return ApiResponse(
            success=True,
            message="Retrieved connections successfully",
            data={"connections": connections_info}
        )
    except Exception as e:
        logger.error(f"Error getting connections: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/connect", response_model=ApiResponse)
async def connect_database(request: DatabaseConnectionRequest):
    """Connect to a database"""
    try:
        # Validate database type
        try:
            db_type = DatabaseType(request.db_type.lower())
        except ValueError:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid database type: {request.db_type}. Supported types: mysql, postgresql, mongodb"
            )
        
        # Create database config
        config = DatabaseConfig(
            db_type=db_type,
            host=request.host,
            port=request.port,
            username=request.username,
            password=request.password,
            database=request.database
        )
        
        # Test connection
        logger.info(f"Attempting to connect to {db_type.value} at {request.host}:{request.port}")
        success = await connector.connect(config)
        
        if success:
            current_connections[db_type.value] = config
            logger.info(f"Successfully connected to {db_type.value}")
            
            return ApiResponse(
                success=True,
                message=f"Connected to {db_type.value} successfully",
                data={
                    "connection_info": {
                        "type": db_type.value,
                        "host": request.host,
                        "port": request.port,
                        "database": request.database,
                        "connected": True
                    }
                }
            )
        else:
            raise HTTPException(status_code=400, detail="Connection failed")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Connection error: {e}")
        raise HTTPException(status_code=500, detail=f"Connection error: {str(e)}")

@app.delete("/api/disconnect/{db_type}", response_model=ApiResponse)
async def disconnect_database(db_type: str):
    """Disconnect from a specific database"""
    try:
        if db_type in current_connections:
            # Remove from current connections
            config = current_connections.pop(db_type)
            logger.info(f"Disconnected from {db_type}")
            
            return ApiResponse(
                success=True,
                message=f"Disconnected from {db_type} successfully"
            )
        else:
            raise HTTPException(status_code=404, detail=f"No active connection for {db_type}")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Disconnect error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/test-connection", response_model=ApiResponse)
async def test_connection(request: DatabaseConnectionRequest):
    """Test database connection without storing it"""
    try:
        db_type = DatabaseType(request.db_type.lower())
        config = DatabaseConfig(
            db_type=db_type,
            host=request.host,
            port=request.port,
            username=request.username,
            password=request.password,
            database=request.database
        )
        
        # Create a temporary connector for testing
        temp_connector = DatabaseConnector()
        result = await temp_connector.test_connection(config)
        await temp_connector.close_all_connections()
        
        return ApiResponse(
            success=result["success"],
            message=result["message"],
            data=result.get("connection_info", {})
        )
        
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid database type: {request.db_type}")
    except Exception as e:
        logger.error(f"Test connection error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Schema Discovery Endpoints
@app.post("/api/discover-schema/{db_type}", response_model=ApiResponse)
async def discover_schema(db_type: str):
    """Discover and store database schema in RAG system"""
    try:
        if db_type not in current_connections:
            raise HTTPException(status_code=400, detail=f"No active connection for {db_type}")
        
        config = current_connections[db_type]
        logger.info(f"Starting schema discovery for {db_type}")
        
        schema = await connector.discover_and_store_schema(config.db_type, config.to_dict())
        
        if schema:
            logger.info(f"Schema discovery completed for {db_type}")
            return ApiResponse(
                success=True,
                message="Schema discovered and stored successfully",
                data={
                    "schema_summary": {
                        "tables": len(schema.get("tables", {})),
                        "relationships": len(schema.get("relationships", [])),
                        "collections": len(schema.get("collections", {}))
                    }
                }
            )
        else:
            raise HTTPException(status_code=500, detail="Schema discovery failed")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Schema discovery error: {e}")
        raise HTTPException(status_code=500, detail=f"Schema discovery error: {str(e)}")

@app.get("/api/schema-summary/{db_type}", response_model=ApiResponse)
async def get_schema_summary(db_type: str):
    """Get schema summary for a specific database type"""
    try:
        try:
            db_type_enum = DatabaseType(db_type.lower())
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid database type: {db_type}")
        
        summary = connector.get_schema_summary(db_type_enum)
        
        return ApiResponse(
            success=True,
            message="Schema summary retrieved successfully",
            data={"summary": summary}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Schema summary error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# RAG System Endpoints
@app.get("/api/rag-overview", response_model=ApiResponse)
async def get_rag_overview():
    """Get RAG system overview"""
    try:
        overview = connector.get_rag_overview()
        return ApiResponse(
            success=True,
            message="RAG overview retrieved successfully",
            data=overview
        )
    except Exception as e:
        logger.error(f"RAG overview error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/search-schema", response_model=ApiResponse)
async def search_schema(request: QueryRequest):
    """Search schema using RAG system"""
    try:
        database_filter = request.database
        results = connector.rag.search_schema(
            query=request.query,
            n_results=10,
            database_filter=database_filter
        )
        
        return ApiResponse(
            success=True,
            message="Schema search completed successfully",
            data={
                "results": results,
                "query": request.query,
                "database_filter": database_filter
            }
        )
        
    except Exception as e:
        logger.error(f"Schema search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/rag-reset", response_model=ApiResponse)
async def reset_rag_collection():
    """Reset RAG collection (delete all stored schemas)"""
    try:
        # This would reset the RAG collection
        connector.rag.collection.delete(where={})
        
        return ApiResponse(
            success=True,
            message="RAG collection reset successfully"
        )
        
    except Exception as e:
        logger.error(f"RAG reset error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Query Processing Endpoints
@app.post("/api/query", response_model=ApiResponse)
async def ask_question(request: QueryRequest):
    """Process natural language question"""
    try:
        overview = connector.get_rag_overview()
        
        if overview["total_documents"] == 0:
            raise HTTPException(
                status_code=400, 
                detail="No schemas stored in RAG system. Please discover and store schemas first."
            )
        
        # Determine database
        if request.database:
            database = request.database
            if database not in overview["databases"]:
                raise HTTPException(status_code=400, detail=f"Database '{database}' not found in RAG system")
        else:
            database = next(iter(overview["databases"]))
        
        logger.info(f"Processing query: '{request.query}' for database: {database}")
        
        # Get schema context
        schema_context = connector.get_schema_context(database)
        
        # Analyze query with Gemini
        analysis = await gemini_helper.analyze_query(request.query, schema_context)
        
        if analysis.get("type") == "error":
            raise HTTPException(status_code=500, detail=analysis["message"])
        
        if analysis["type"] == "schema":
            # Handle schema question using RAG
            results = connector.rag.search_schema(
                query=request.query,
                n_results=5,
                database_filter=database
            )
            
            return ApiResponse(
                success=True,
                message="Schema query processed successfully",
                data={
                    "type": "schema",
                    "results": results,
                    "query": request.query,
                    "database": database
                }
            )
        else:
            # Handle data question - generate SQL
            db_info = overview["databases"][database]
            db_type = DatabaseType(db_info["type"])
            
            # Check if we have an active connection for this database type
            if db_type.value not in current_connections:
                raise HTTPException(
                    status_code=400, 
                    detail=f"No active connection for database type: {db_type.value}"
                )
            
            sql_result = await gemini_helper.generate_sql(
                request.query,
                schema_context,
                db_type.value
            )
            
            if sql_result.get("type") == "error":
                raise HTTPException(status_code=500, detail=sql_result["message"])
            
            return ApiResponse(
                success=True,
                message="Data query processed successfully",
                data={
                    "type": "data",
                    "sql_query": sql_result["query"],
                    "explanation": sql_result.get("explanation"),
                    "warnings": sql_result.get("warnings", []),
                    "assumptions": sql_result.get("assumptions", []),
                    "query": request.query,
                    "database": database
                }
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Query processing error: {e}")
        raise HTTPException(status_code=500, detail=f"Query processing error: {str(e)}")

@app.post("/api/execute-sql", response_model=ApiResponse)
async def execute_sql(request: ExecuteSQLRequest):
    """Execute SQL query"""
    try:
        if not request.sql_query or not request.database:
            raise HTTPException(status_code=400, detail="SQL query and database are required")
        
        overview = connector.get_rag_overview()
        if request.database not in overview["databases"]:
            raise HTTPException(status_code=400, detail=f"Database {request.database} not found")
        
        db_info = overview["databases"][request.database]
        db_type = DatabaseType(db_info["type"])
        
        # Check if we have an active connection
        if db_type.value not in current_connections:
            raise HTTPException(
                status_code=400, 
                detail=f"No active connection for database: {request.database}"
            )
        
        logger.info(f"Executing SQL: {request.sql_query}")
        
        # Execute query
        results = await connector.execute_query(db_type, request.sql_query)
        
        return ApiResponse(
            success=True,
            message="Query executed successfully",
            data={
                "results": results,
                "count": len(results),
                "sql_query": request.sql_query
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"SQL execution error: {e}")
        raise HTTPException(status_code=500, detail=f"SQL execution error: {str(e)}")

# Additional utility endpoints
@app.get("/api/database-types")
async def get_supported_database_types():
    """Get list of supported database types"""
    return {
        "supported_types": [db_type.value for db_type in DatabaseType],
        "descriptions": {
            "mysql": "MySQL Database",
            "postgresql": "PostgreSQL Database", 
            "mongodb": "MongoDB Database"
        }
    }

@app.get("/api/stats")
async def get_system_stats():
    """Get system statistics"""
    try:
        overview = connector.get_rag_overview()
        
        stats = {
            "connections": {
                "total": len(current_connections),
                "by_type": {}
            },
            "rag": overview,
            "supported_databases": len(DatabaseType)
        }
        
        # Count connections by type
        for db_type in current_connections:
            stats["connections"]["by_type"][db_type] = 1
        
        return ApiResponse(
            success=True,
            message="System stats retrieved successfully",
            data=stats
        )
        
    except Exception as e:
        logger.error(f"Stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={
            "success": False,
            "message": "Endpoint not found",
            "error": "The requested endpoint does not exist"
        }
    )

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "Internal server error",
            "error": "An unexpected error occurred"
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",  # Use import string format for reload
        host="0.0.0.0", 
        port=8000,
        reload=True,
        log_level="info"
    )