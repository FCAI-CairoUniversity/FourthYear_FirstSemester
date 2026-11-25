import json


def read_json_file(filename):
    """
    Reads and parses JSON data from a file.
    Returns the parsed data or None if an error occurs.
    """
    try:
        with open(filename, "r") as file:
            data = json.load(file)  # Parse JSON to Python objects
        return data
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found.")
        return None
    except json.JSONDecodeError:
        print(f"Error: File '{filename}' is not valid JSON.")
        return None


def main():
    filename = "student_data.json"  # Change to your actual filename
    data = read_json_file(filename)
    if data is not None:
        print("Parsed JSON data:")
        print(json.dumps(data, indent=4))  # Pretty-print JSON
    else:
        print("No data to display.")


if __name__ == "__main__":
    main()
