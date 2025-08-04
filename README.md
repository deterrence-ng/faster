# Faster - A FastAPI Template

A template for building FastAPI applications quickly and efficiently.

```bash
# Clone the repository
git clone https://github.com/deterrence-ng/faster.git

# Remove the .git directory
rm -rf faster/.git

# Rename the directory to your project name
mv faster my_project_name

# Navigate into your project directory
cd my_project_name

# Rename the .env.example file to .env
# Update the .env file with your environment variables
mv .env.example .env

# Install dependencies using uv
uv sync

# Activate the virtual environment
source .venv/bin/activate

# Run the initial alembic migrations
alembic upgrade head

# Initialize Admin User to obtain Super Admin password
python initialize.py

# Start the FastAPI application
uvicorn app.main:app --reload

```
