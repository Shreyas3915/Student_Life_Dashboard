import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RAW_CSV = ROOT / 'student_data_raw.csv'
CLEAN_CSV = ROOT / 'student_data_clean.csv'
JSON_FILE = ROOT / 'student_data.json'
JS_FILE = ROOT / 'student_data.js'

BRANCH_MAP = {
    'cs': 'Computer Science',
    'ds': 'Data Science',
    'ece': 'Electronics',
    'mech': 'Mechanical',
    'civil': 'Civil'
}

NUMERIC_FIELDS = {
    'sem': int,
    'cgpa': float,
    'att': int,
    'backlogs': int,
    'asn': int,
    'study': float,
    'sleep': float,
    'screen': float,
    'exercise': int,
    'friends': int,
    'hostel': int,
    'stress': int,
    'pressure': int,
    'motivation': int,
    'club': int,
    'intern': int,
    'proj': int,
    'cert': int,
    'coding': int,
}


def clamp(value, minimum=0, maximum=100):
    return max(minimum, min(maximum, int(round(value))))


def clean_branch(raw_branch: str) -> str:
    branch = raw_branch.strip()
    key = branch.lower()
    return BRANCH_MAP.get(key, branch.title())


def predict(student: dict) -> dict:
    burnout = clamp(
        student['stress'] * 7
        + student['pressure'] * 4
        + (10 - student['sleep']) * 3
        + student['backlogs'] * 4
        + (100 - student['att']) * 0.3
        + student['screen'] * 1.5
        + (10 - student['motivation']) * 4
        + student['hostel'] * 3
        - student['exercise'] * 2
        - student['friends'] * 1.5
        - student['study'] * 1
        + (7 - student['cgpa']) * 2
    )
    placement = clamp(
        student['cgpa'] * 6
        + student['coding'] * 3
        + student['intern'] * 8
        + student['proj'] * 3
        + student['cert'] * 2
        + student['att'] * 0.2
        + student['motivation'] * 1.5
        - student['backlogs'] * 2
        + student['study'] * 1
    )
    backlog_risk = clamp(
        student['backlogs'] * 8
        + (100 - student['att']) * 0.4
        + (10 - student['cgpa']) * 4
        + student['stress'] * 3
        + (100 - student['asn']) * 0.3
        + (8 - student['sleep']) * 2
        - student['study'] * 2
        - student['motivation'] * 2
    )
    loneliness = clamp(
        (10 - student['friends']) * 6
        + student['hostel'] * 4
        + student['stress'] * 2
        + student['screen'] * 1.5
        - student['club'] * 4
        - student['exercise'] * 2
        + (8 - student['sleep']) * 2
    )
    productivity = clamp(
        student['study'] * 5
        + student['motivation'] * 4
        + student['att'] * 0.3
        - student['stress'] * 2
        - student['screen'] * 1.5
        + student['exercise'] * 2
        + student['cgpa'] * 2
    )
    return {
        'burnout': burnout,
        'placement': placement,
        'backlogRisk': backlog_risk,
        'loneliness': loneliness,
        'productivity': productivity,
    }


def preprocess_row(row: dict) -> dict:
    student = {}
    for key, value in row.items():
        if key == 'branch':
            student[key] = clean_branch(value)
        elif key in NUMERIC_FIELDS:
            student[key] = NUMERIC_FIELDS[key](value)
        else:
            student[key] = value.strip()

    student.update(predict(student))
    student['branch'] = student['branch'] if student['branch'] in BRANCH_MAP.values() else student['branch']
    return student


def load_raw_data() -> list[dict]:
    with RAW_CSV.open(newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return [preprocess_row(row) for row in reader]


def write_clean_csv(data: list[dict]) -> None:
    fieldnames = list(data[0].keys()) if data else []
    with CLEAN_CSV.open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)


def write_json(data: list[dict]) -> None:
    with JSON_FILE.open('w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)


def write_js(data: list[dict]) -> None:
    payload = json.dumps(data, indent=2)
    content = f'// Auto-generated dataset file. Run preprocess_student_data.py to regenerate.\nconst DATA = {payload};\n'
    with JS_FILE.open('w', encoding='utf-8') as f:
        f.write(content)


def main() -> None:
    data = load_raw_data()
    write_clean_csv(data)
    write_json(data)
    write_js(data)
    print(f'Generated {CLEAN_CSV.name}, {JSON_FILE.name}, and {JS_FILE.name} from {RAW_CSV.name}.')


if __name__ == '__main__':
    main()
