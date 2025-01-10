import argparse
import pandas as pd
import matplotlib.pyplot as plt
from langchain.prompts import PromptTemplate
from langchain_openai import OpenAI  # Updated import to langchain_openai
import os
import uuid

# Initialize the OpenAI LLM
llm = OpenAI(temperature=0)
COMMON_IMPORTS = {'base64', 'json', 'pandas', 'numpy', 'datetime'}
SPECIAL_IMPORTS = {'matplotlib', 'seaborn'}

# Define a prompt template
prompt = PromptTemplate(
    input_variables=["columns", "query", "file_path", "com_imports", "sp_imports"],
    template=(
        "You are a Python data analysis assistant. Using the dataset columns {columns}, "
        "If the query is not related to matplotlib, without importing {sp_imports} provide a detailed response as plain text. "
        "If the query is related to matplotlib, write ONLY the Python code as an output by importing all of {com_imports} and {sp_imports} to: {query}. "
        "Do not write any text explanation except the code and the code should run directly without errors. "
        "Use the {file_path} as path in the generated code. "
        "The output should match the expected type, such as a plot for matplotlib queries or a text response for others. "
        "For matplotlib code, add functionality to save the plot. "
        "# Save the plot\noutput_path = 'output_plot_' + str(uuid.uuid4()) + '.png' \nplt.savefig(output_path)\nplt.show()"
    ),
)

# Define a safe execution environment
def execute_code(code, globals_dict, locals_dict):
    allowed_globals = {
        '__builtins__': __builtins__,
        'base64': __import__('base64'),
        'json': __import__('json'),
        'pandas': pd,
        'numpy': __import__('numpy'),
        'datetime': __import__('datetime'),
        'matplotlib': plt,
        'seaborn': __import__('seaborn'),
        'uuid': uuid
    }
    try:
        print("Executing generated code.")
        exec(code, {k: allowed_globals[k] for k in allowed_globals}, locals_dict)
    except Exception as e:
        print(f"Error executing code: {e}")
        raise

# Function to retry code generation and execution with a limit
def retry_execution(prompt, llm, error_message, globals_dict, locals_dict, columns, user_query, file_path, max_retries=3):
    retry_count = 0
    while retry_count < max_retries:
        print(f"Retrying due to error: {error_message} (Attempt {retry_count + 1}/{max_retries})")
        response = prompt.format(columns=columns, query=user_query + f" (Resolve the error: {error_message})", file_path=file_path, 
                                 com_imports=COMMON_IMPORTS, sp_imports=SPECIAL_IMPORTS)
        response = llm.invoke(response)
        print(f"Generated new code on retry {retry_count + 1}: {response}")
        try:
            execute_code(response, globals_dict, locals_dict)
            return
        except Exception as e:
            error_message = str(e)
            retry_count += 1
    print(f"Exceeded maximum retries ({max_retries}). Unable to resolve the issue.")

# Function to validate matplotlib code
def validate_code(code):
    try:
        # Check for unsafe imports or malicious code
        disallowed_imports = ["io", "os", "subprocess", "sys", "importlib", "pickle", "shutil", "tempfile"]
        for disallowed in disallowed_imports:
            if disallowed in code:
                raise ValueError(f"Disallowed import detected: {disallowed}")
        compile(code, '<string>', 'exec')
        print("Code validation successful.")
    except (SyntaxError, ValueError) as e:
        print(f"Code validation failed: {e}")
        return False, str(e)
    return True, None

# Function to run a dry-run mode
def dry_run_code(code):
    try:
        print("Dry-run: Compiling the code to check for errors...")
        compile(code, '<string>', 'exec')
        print("Dry-run successful. Code is syntactically correct.")
    except SyntaxError as e:
        print(f"Dry-run failed: {e}")
        raise

# Main function
def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Run a data analysis task with an LLM.")
    parser.add_argument("file_path", type=str, help="Path to the input CSV file")
    args = parser.parse_args()

    # Load the dataset
    if not os.path.exists(args.file_path):
        print(f"Error: File not found at {args.file_path}")
        return

    session_id = str(uuid.uuid4())

    print(f"Session ID: {session_id}")

    file_path = args.file_path
    df = pd.read_csv(args.file_path)
    columns = list(df.columns)

    while True:
        # Prompt the user for a query
        user_query = input("What do you want to analyze about the data (type 'exit' or 'quit' to end): ")
        if user_query.lower() in ["exit", "quit"]:
            print("Ending the session. Goodbye!")
            break

        print(f"User query: {user_query}")
        response = prompt.format(columns=columns, query=user_query, file_path=file_path,
                                 com_imports=COMMON_IMPORTS, sp_imports=SPECIAL_IMPORTS)
        response = llm.invoke(response)
        print(f"Generated response: {response}")

        # Validate the code
        is_valid, error_message = validate_code(response)
        if not is_valid:
            retry_execution(prompt, llm, error_message, globals(), {}, columns, user_query, file_path)
            continue

        # Check if the response contains matplotlib code
        if "matplotlib" in response or "plt" in response:
            print("Generated matplotlib code detected. Performing dry-run...")
            try:
                dry_run_code(response)
                print("Dry-run successful. Executing the code...")
                globals_dict = {"df": df, "plt": plt, "file_path": args.file_path, "uuid": uuid}
                locals_dict = {}
                execute_code(response, globals_dict, locals_dict)
                print(f"Plot saved with a unique identifier in the current directory.")
            except Exception as e:
                retry_execution(prompt, llm, str(e), globals_dict, locals_dict, columns, user_query, file_path)
        else:
            print("Response:")
            print(response)

if __name__ == "__main__":
    main()
