# inzpraca

# 🛠️ Django API Project

REST API built with Django and Django REST Framework. This project includes user authentication, role-based permissions, and automatic API documentation with Swagger.

## 🚀 Local Development Setup

### ✅ Requirements

- Python 3.10–3.12 (⚠️ Python 3.13 may cause issues with some packages)
- pip (Python package installer)
- virtualenv (optional but recommended)

### 📦 Setup Instructions

1. Clone the repository

   ```bash
   git clone <REPO_URL>
   cd <project_folder>
   ```

2. (Optional) Create and activate a virtual environment

   ```bash
   python -m venv venv
   # On Linux/macOS:
   source venv/bin/activate
   # On Windows:
   venv\Scripts\activate
   ```

3. Install dependencies

   ```bash
   pip install -r requirements.txt
   ```

4. Apply database migrations

   ```bash
   python manage.py migrate
   ```

5. (Optional) Create a superuser

   ```bash
   python manage.py createsuperuser
   ```

6. Run the development server
   ```bash
   python manage.py runserver
   ```

Visit the app at:  
http://127.0.0.1:8000/

## 📘 API Documentation

Swagger UI is available at:  
http://127.0.0.1:8000/swagger/

## 🧪 Run Tests

```bash
python manage.py test
```

## 🧾 License

MIT License (or specify your own)
