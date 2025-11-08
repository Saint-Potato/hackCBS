import google.generativeai as genai
from typing import Dict, Any, List, Optional
import os
from dotenv import load_dotenv
import logging
import json
import re

logger = logging.getLogger(__name__)


class GeminiHelper:
    """Helper class for Gemini API integration"""

    def __init__(self):
        """Initialize Gemini API"""
        load_dotenv()

        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment variables")

        genai.configure(api_key=api_key)

        self.model = genai.GenerativeModel(
            model_name=os.getenv("GEMINI_MODEL", "gemini-pro"),
            generation_config={
                "max_output_tokens": int(os.getenv("MAX_OUTPUT_TOKENS", "2048")),
                "temperature": float(os.getenv("TEMPERATURE", "0.7")),
            },
        )

        logger.info(
            f"Initialized Gemini with model: {os.getenv('GEMINI_MODEL', 'gemini-pro')}"
        )

    async def analyze_query(self, query: str, schema_context: str) -> Dict[str, Any]:
        """Analyze query to determine if it's about schema or data"""
        system_prompt = """
        You are a database expert assistant. Analyze the user's query and determine if it's asking about database schema or actual data.
        
        Schema Context:
        {schema_context}
        
        Rules:
        - If the query asks for counts, specific records, values, or data analysis (like "how many students", "show me users", "average price") -> classify as "data"
        - If the query asks about structure, tables, columns, relationships (like "what tables exist", "show table structure") -> classify as "schema"
        
        Respond with only one word: either "data" or "schema"
        """

        prompt = system_prompt.format(schema_context=schema_context)

        try:
            response = await self.model.generate_content_async(
                [prompt, f"User Query: {query}"]
            )

            analysis_type = response.text.strip().lower()

            return {
                "type": "data" if "data" in analysis_type else "schema",
                "raw_response": response.text,
            }

        except Exception as e:
            logger.error(f"Error analyzing query with Gemini: {e}")
            return {"type": "error", "message": str(e)}

    async def generate_sql(
        self, query: str, schema_context: str, db_type: str
    ) -> Dict[str, Any]:
        """Generate SQL query based on natural language input"""
        system_prompt = """
        You are a SQL expert. Generate a SQL query for the user's request using the provided database schema.
        
        Database Type: {db_type}
        
        Schema Information:
        {schema_context}
        
        User Request: {query}
        
        Instructions:
        1. Generate ONLY a valid SQL query - no explanations or extra text
        2. Use proper SQL syntax for {db_type}
        3. Only use tables and columns that exist in the schema
        4. For count queries, use COUNT(*) or COUNT(column_name)
        5. Include appropriate WHERE clauses if needed
        
        Generate only the SQL query, nothing else:
        """

        prompt = system_prompt.format(
            db_type=db_type, schema_context=schema_context, query=query
        )

        try:
            response = await self.model.generate_content_async(prompt)

            # Extract SQL from response
            sql_query = self._extract_sql_from_response(response.text)

            if sql_query:
                return {
                    "query": sql_query,
                    "explanation": f"Generated SQL query to {query.lower()}",
                    "assumptions": ["Used available schema information"],
                    "warnings": ["Please verify the query before execution"],
                }
            else:
                return {
                    "type": "error",
                    "message": "Could not extract valid SQL from Gemini response",
                    "raw_response": response.text,
                }

        except Exception as e:
            logger.error(f"Error generating SQL with Gemini: {e}")
            return {"type": "error", "message": str(e)}

    def _extract_sql_from_response(self, response: str) -> Optional[str]:
        """Extract SQL query from Gemini response"""
        try:
            # Clean the response
            response = response.strip()

            # Remove markdown code blocks if present
            if "```sql" in response:
                # Extract SQL from markdown code block
                match = re.search(
                    r"```sql\s*\n(.*?)\n```", response, re.DOTALL | re.IGNORECASE
                )
                if match:
                    return match.group(1).strip()

            if "```" in response:
                # Extract from generic code block
                match = re.search(r"```\s*\n?(.*?)\n?```", response, re.DOTALL)
                if match:
                    return match.group(1).strip()

            # Look for SQL keywords
            sql_keywords = ["SELECT", "INSERT", "UPDATE", "DELETE", "WITH"]
            lines = response.split("\n")

            for line in lines:
                line = line.strip()
                if any(line.upper().startswith(keyword) for keyword in sql_keywords):
                    return line

            # If no specific SQL found, check if the entire response looks like SQL
            if any(keyword in response.upper() for keyword in sql_keywords):
                # Clean up common extra characters
                cleaned = re.sub(
                    r"^[^\w]*", "", response
                )  # Remove leading non-word chars
                cleaned = re.sub(
                    r"[^\w\s\(\)\*\,\.\=\<\>\'\";-]*$", "", cleaned
                )  # Remove trailing junk
                return cleaned.strip()

            return None

        except Exception as e:
            logger.error(f"Error extracting SQL: {e}")
            return None

    async def explain_data_results(
        self, query: str, results: List[Dict], schema_context: str
    ) -> str:
        """Generate natural language explanation of query results"""
        system_prompt = """
        You are a data analyst. Explain the query results in simple, business-friendly language.
        
        Original Query: {query}
        Number of Results: {result_count}
        
        Sample Results (first few rows):
        {results_sample}
        
        Provide a brief, clear explanation of what these results mean.
        """

        # Convert results to string representation
        results_sample = "\n".join([str(row) for row in results[:3]])

        prompt = system_prompt.format(
            query=query, result_count=len(results), results_sample=results_sample
        )

        try:
            response = await self.model.generate_content_async(prompt)
            return response.text.strip()

        except Exception as e:
            logger.error(f"Error explaining results with Gemini: {e}")
            return f"Found {len(results)} result(s) for your query."

    async def analyze_visualization_query(
        self, query: str, schema_context: str
    ) -> Dict[str, Any]:
        """Analyze if query needs visualization and generate appropriate response"""

        system_prompt = f"""
        You are a data visualization expert. Analyze this query: "{query}"
        
        Schema Context: {schema_context}
        
        Determine:
        1. Does this query need visualization? Look for keywords like "chart", "plot", "graph", "visualize", "show trends"
        2. What type of chart would be best? (bar, line, pie, scatter, histogram)
        3. What SQL query should generate the data for visualization?
        4. Is this a schema query or data query?
        
        Chart type guidelines:
        - "over time", "timeline", "trends" = line chart
        - "distribution", "frequency" = histogram  
        - "comparison", "by category", "count by" = bar chart
        - "proportion", "percentage", "share of" = pie chart
        - "correlation", "relationship between" = scatter plot
        
        Respond in JSON format:
        {{
            "needs_visualization": true/false,
            "chart_type": "bar|line|pie|scatter|histogram",
            "query_type": "data|schema", 
            "sql_query": "SELECT ...",
            "explanation": "brief explanation of what will be visualized"
        }}
        """

        try:
            response = await self.model.generate_content_async(system_prompt)
            result = json.loads(
                response.text.strip().replace("```json", "").replace("```", "")
            )
            return result
        except Exception as e:
            logger.error(f"Visualization analysis error: {e}")
            return {
                "needs_visualization": False,
                "chart_type": "bar",
                "query_type": "data",
                "sql_query": None,
                "explanation": "Could not analyze visualization requirements",
            }

    def _parse_gemini_response(self, response: str) -> Dict[str, Any]:
        """Parse and structure Gemini's response (keeping for compatibility)"""
        return {
            "type": (
                "data"
                if any(
                    word in response.lower()
                    for word in ["count", "show", "find", "get", "average"]
                )
                else "schema"
            ),
            "raw_response": response,
        }

    def _parse_sql_response(self, response: str) -> Dict[str, Any]:
        """Parse and validate SQL response (keeping for compatibility)"""
        sql_query = self._extract_sql_from_response(response)

        return {
            "query": sql_query,
            "explanation": "Generated SQL query",
            "assumptions": [],
            "warnings": [],
            "raw_response": response,
        }

    async def generate_natural_response(self, context: str) -> Dict[str, Any]:
        """Generate a natural language response based on context"""
        try:
            response = self.model.generate_content(context)

            return {
                "text": response.text,
                "metadata": {
                    "model": "gemini-pro",
                    "safety_ratings": (
                        [r.to_dict() for r in response.safety_ratings]
                        if hasattr(response, "safety_ratings")
                        else []
                    ),
                },
            }
        except Exception as e:
            return {
                "text": "I found some results but couldn't generate a natural response. Here are the raw results instead.",
                "error": str(e),
            }
