# Build a Data Processing Pipeline

Create a Python data processing pipeline that reads, transforms, validates, and outputs data. This tests your ability to handle multi-step data workflows.

## Input Data

You'll work with this sample CSV data (create it in your script):

```csv
id,name,email,age,department,salary,hire_date
1,John Smith,john@example.com,32,Engineering,75000,2020-03-15
2,Jane Doe,jane.doe@example,28,Marketing,55000,2021-07-22
3,Bob Wilson,bob@example.com,45,Engineering,95000,2018-01-10
4,Alice Brown,alice@example.com,29,Sales,60000,2022-02-28
5,Charlie Davis,,35,Engineering,80000,2019-11-05
6,Eve Johnson,eve@example.com,-5,HR,50000,2023-04-12
7,Frank Miller,frank@example.com,52,Engineering,120000,2017-06-30
8,Grace Lee,grace@example.com,31,Marketing,58000,2021-09-15
9,Henry Taylor,invalid-email,40,Sales,70000,2020-08-20
10,Ivy Chen,ivy@example.com,27,Engineering,72000,2022-11-01
```

## Pipeline Steps

### Step 1: Read & Parse
- Read CSV data (can be embedded in script)
- Parse into structured records
- Handle missing values

### Step 2: Validate
- Email must contain @ and .
- Age must be between 18 and 100
- Salary must be positive
- Create validation report of invalid records

### Step 3: Transform
- Add `email_domain` field (extract from email)
- Add `years_employed` field (from hire_date to today)
- Add `salary_band` field: "Junior" (<60k), "Mid" (60-90k), "Senior" (>90k)
- Normalize department names to uppercase

### Step 4: Aggregate
- Count employees per department
- Average salary per department
- Average age per department

### Step 5: Output
Create three output files:

1. `valid_employees.json` - Valid records with transformations
2. `invalid_records.json` - Records that failed validation with reasons
3. `department_summary.json` - Aggregated statistics

## Example Output

`valid_employees.json`:
```json
[
  {
    "id": 1,
    "name": "John Smith",
    "email": "john@example.com",
    "email_domain": "example.com",
    "age": 32,
    "department": "ENGINEERING",
    "salary": 75000,
    "salary_band": "Mid",
    "hire_date": "2020-03-15",
    "years_employed": 4
  }
]
```

`invalid_records.json`:
```json
[
  {
    "id": 2,
    "name": "Jane Doe",
    "errors": ["Invalid email format"]
  },
  {
    "id": 6,
    "name": "Eve Johnson", 
    "errors": ["Age must be between 18 and 100"]
  }
]
```

`department_summary.json`:
```json
{
  "ENGINEERING": {
    "count": 4,
    "avg_salary": 85500,
    "avg_age": 39
  }
}
```

## Technical Requirements

- Python 3 standard library only (csv, json, datetime)
- Single Python file: `pipeline.py`
- Run with: `python pipeline.py`
- Print progress: "Step 1: Reading data...", etc.

## Deliverables

1. `pipeline.py` - The complete pipeline
2. Three output JSON files created when run

## Evaluation

- All pipeline steps execute
- Validation catches the 3 invalid records
- Transformations applied correctly
- Aggregations calculated correctly
- Clean, readable code
