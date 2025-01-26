from flask import Flask, request, jsonify
from sqlalchemy import create_engine, text
from typing_extensions import TypedDict, Annotated
from langchain import hub
from langchain_openai import ChatOpenAI
from flask_cors import CORS
import re

# Flask app setup
app = Flask(__name__)
CORS(app)

# Database connection setup
db_uri = "mysql+mysqlconnector://rutuja13:Ghanekar#1328@localhost:3306/info_db"  # Replace with your DB URI
engine = create_engine(db_uri)

# LLM setup
llm = ChatOpenAI(
    model="gpt-4o-mini",
    api_key="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"
)

# Pull the query prompt template
query_prompt_template = hub.pull("langchain-ai/sql-query-system-prompt")

# Fetch table names
with engine.connect() as conn:
    result = conn.execute(text("SHOW TABLES;"))
    table_names = [row[0] for row in result]

# TypedDict definitions
class State(TypedDict):
    question: str
    query: str
    result: str
    answer: str

class QueryOutput(TypedDict):
    """Generated SQL query."""
    query: Annotated[str, ..., "Syntactically valid SQL query."]

# Helper function to adjust column names
def adjust_query_columns(query: str) -> str:
    """
    Adjust the column names in the SQL query to match the correct schema.

    Args:
        query (str): The original SQL query.

    Returns:
        str: The adjusted SQL query with the correct column names.
    """
    column_replacements = {
        "products.price": "products.product_price",
        "products.name": "products.product_name",
        "products.brand": "products.brand_name",
        "products.id" : "products.product_id",
        "suppliers.id":"suppliers.supplier_id",
        "suppliers.brand": "suppliers.brand_name",
        "suppliers.name": "suppliers.supplier_name"
    }
    
    # Replace whole word matches to avoid partial replacements
    for old_column, new_column in column_replacements.items():
        # \b ensures it matches as a whole word
        query = re.sub(rf'\b{re.escape(old_column)}\b', new_column, query)
    
    return query

# Helper functions
def write_query(question: str):
    """Generate SQL query from user question."""
    prompt = query_prompt_template.invoke(
        {
            "dialect": engine.dialect,
            "top_k": 10,
            "table_info": table_names,
            "input": question,
        }
    )
    structured_llm = llm.with_structured_output(QueryOutput)
    result = structured_llm.invoke(prompt)
    # Replace LIMIT 10 and adjust column names
    adjusted_query = adjust_query_columns(result["query"].replace("LIMIT 10", ""))
    return adjusted_query

def execute_query(query: str):
    """Execute SQL query and return JSON-serializable results."""
    try:
        with engine.connect() as conn:
            result = conn.execute(text(query)).fetchall()       #fetches data from sql db n shws o/p in tuple
            print("333333333333333333333",result)
            # Convert the result to a list of dictionaries
            rows = [item[0] for item in result]
            print("rows",rows)
            # rows=""
            # for row in result:
            #     rows += row[0]
            return rows
    except Exception as e:
        return {"error": str(e)}

def generate_answer(question: str, query: str, result: any):
    """Generate a natural language answer."""
    prompt = (
        "Given the following user question, corresponding SQL query, "
        "and SQL result, answer the user question.\n\n"
        f'Question: {question}\n'
        f'SQL Query: {query}\n'
        f'SQL Result: {result}'
    )
    response = llm.invoke(prompt)
    return response.content

# API endpoint
@app.route('/ask', methods=['POST'])
def ask_question():
    """API endpoint to process user question."""
    try:
        # Get user question from POST request
        data = request.get_json()           
        print("asdgtrfyguh",data)
        question = data.get("query", "").strip()        #strip() removes comma colon question mark
        print("asdfgh",question)
        if not question:
            return jsonify({"error": "Question is required"}), 400

        # Generate SQL query
        query = write_query(question)
        print("111111111111111111111111",query)

        # Execute SQL query
        result = execute_query(query)
        print("2222222222222222222",result)

        # Check for errors in the query result
        if isinstance(result, dict) and "error" in result:
            return jsonify({
                "question": question,
                "query": query,
                "result": result,
                "answer": "An error occurred during SQL execution. Please check the query or database."
            })

        # Generate answer
        answer = generate_answer(question, query, result)

        # Return the result
        return jsonify({
            "answer": answer
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Run Flask app
if __name__ == '__main__':
    app.run(debug=True, port=5000)