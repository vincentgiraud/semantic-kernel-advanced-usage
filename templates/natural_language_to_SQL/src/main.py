import sys
import asyncio
from rich.console import Console
console = Console()
import json
import os
import sys
sys.path.append("./")
sys.path.append("../")

from src.process.sql_process import SqlProcess
from src.utils.chat_helpers import initialize_kernel



console = Console()

prompt_template = """You are a helpful assistant, you will be given a query, and a context from our SQL database. Your task is to formulate a final answer based on the query and the context from the database.

Query: {{$query}}

DB Context:
{{$context}}

"""



async def main():
    # Get query from command line argument
    if len(sys.argv) < 2:
        console.print("[red]Error: Please provide a query as a command line argument[/red]")
        console.print("Usage: python src/main.py \"your natural language query here\"")
        sys.exit(1)
        
    query = sys.argv[1]
    kernel = await initialize_kernel()

    # Define a semantic function (prompt) to generate a TL;DR summary
    final_answer_fn = kernel.add_function(
        prompt=prompt_template, 
        function_name="db_answer", 
        plugin_name="db_helper"
    )

    sql_process = SqlProcess(kernel)
    await sql_process.start(query)    

    if os.path.exists("response.json"):
        with open("response.json", "r") as f:
            sql_result = f.read()
        sql_result = json.loads(sql_result)
        if sql_result["query"] == query:
            sql_result = sql_result["response"]
        else:            
            sql_result = "No response found."
    else:
        sql_result = "No response found."

    console.print("[purple]SQL Result:[/purple]")
    console.print(sql_result)

    final_answer = await kernel.invoke(final_answer_fn, query=query, context=str(sql_result))
    console.print("[green]Final Answer:[/green]")
    console.print(str(final_answer))

    return final_answer
    

if __name__ == "__main__":
    asyncio.run(main())
