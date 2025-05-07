# Project Setup

## Prerequisites
- Python 3.7 or higher
- `pip` (Python package manager)

## Step 1: Create a Virtual Environment

### Windows
```bash
python -m venv .venv
```

### Linux / macOS
```bash
python3 -m venv .venv
```

## Step 2: Activate the Virtual Environment

### Windows
```bash
.venv\Scripts\activate
```

### Linux / macOS
```bash
source .venv/bin/activate
```

> **Note:** To deactivate the virtual environment at any point, simply run:
```bash
deactivate
```

## Step 3: Install Required Packages

Ensure you have a `requirements.txt` file with all necessary dependencies for the project. Install them using the following command:

```bash
pip install -r requirements.txt
```

## Step 4: Make Database, Run migrations and Create an Admin User


First make a database name `homely` in postgres and then run this command after that in terminal

```bash
alembic upgrade head
```
The above command create all database tables into your `homely` database.

If you have a script for creating an admin user (`create_super_admin.py`), you can run it to initialize the admin account.

### Windows
```bash
python create_super_admin.py
```

### Linux / macOS
```bash
python3 create_super_admin.py
```

You will be prompted to enter the necessary details (e.g., username, password) during this step.

## Step 5: Run the Application

Before running check the `.env` file located in the root of project. Change this line according to user own credentials:

`SQLALCHEMY_DATABASE_URI=username:password@localhost:5432/homely`



Once the setup is complete, you can run the FastAPI application using `uvicorn`.

### Windows
```bash
uvicorn app.main:app --host 0.0.0.0 --reload
```

### Linux / macOS
```bash
uvicorn app.main:app --host 0.0.0.0 --reload
```

This will start the application in development mode with hot-reloading enabled.

## Additional Information

- **Access the API**: Once the application is running, you can access it in your browser or through tools like `curl` or Postman at:
  ```
  http://127.0.0.1:8000
  ```

- **API Documentation**: FastAPI provides interactive documentation through Swagger. You can view it at:
  ```
  http://127.0.0.1:8000/docs
  ```

- **Alternative Documentation**: For ReDoc-based API docs, visit:
  ```
  http://127.0.0.1:8000/redoc
  ```

## Troubleshooting

- **Virtual Environment Issues**: If you encounter issues activating the virtual environment, ensure you are using the correct command for your operating system (Windows vs. Linux/macOS).
  
- **Dependency Errors**: If dependencies fail to install, check the `requirements.txt` file for missing or incorrect package names, and try running `pip install <package>` for individual packages.

- **Admin Creation**: If the `create_super_admin.py` script fails, ensure the script is compatible with your current Python version and all necessary libraries are installed.
