import json


def read_json_file(filename):
    try:
        with open(filename, "r") as file:
            data = json.load(file)
        return data
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found.")
        return None
    except json.JSONDecodeError:
        print(f"Error: File '{filename}' contains invalid JSON.")
        return None


def print_student_details(student_data):
    student = student_data["student"]
    print(f"Name: {student['name']}")
    print(f"Age: {student['age']}")
    print(f"Graduated: {student['isGraduated']}")
    print(f"City: {student['address']['city']}")
    print(f"Country: {student['address']['country']}")
    print("Subjects:")
    for subject in student["subjects"]:
        print(f"  - {subject['name']}: {subject['grade']}")


def main():
    filename = "student_data.json"
    data = read_json_file(filename)
    if data is not None:
        print_student_details(data)
    else:
        print("No data to display.")


if __name__ == "__main__":
    main()
