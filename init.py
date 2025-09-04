def init():
    try:
        with open("log.log", "w", encoding='utf-8') as log_file:
            log_file.write("")  # Clear the log file
        with open("error.log", "w", encoding='utf-8') as error_log:
            error_log.write("")  # Clear the error log file
        with open("data.json", "w", encoding='utf-8') as data_file:
            data_file.write("{}") # Initialize empty JSON object
        with open("api_keys.env", "w", encoding='utf-8') as api_file:
            contents = """# api_keys.env
NOTION_API_KEY=your_api_key_here
"""
            api_file.write(contents)
    except Exception as e:
        print(f"Error occurred during initialization: {str(e)}")

if __name__ == "__main__":
    init()
