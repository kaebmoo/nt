# Revenue Web Application Setup Instructions (Refactored)

This document provides a complete guide to setting up and running the refactored Revenue Web application.

### **1. Prerequisites**

*   Python 3.8+
*   Docker and Docker Compose (for running Redis)
*   `pip` for installing Python packages

### **2. Installation**

**a. Create a Virtual Environment**
It's highly recommended to use a virtual environment.

```bash
# Create a virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate
```

**b. Install Python Dependencies**
Install all the required packages from `requirements.txt`.

```bash
pip install -r requirements.txt
```

### **3. Configuration**

**a. Set Up Environment Variables**
The application uses a `.env` file for configuration.

```bash
# Copy the example file
cp .env.example .env
```

**b. Edit the `.env` file:**
Open the newly created `.env` file and fill in the required values:

*   `SECRET_KEY`: **This is critical.** Generate a long, random string. You can use `python -c 'import secrets; print(secrets.token_hex(16))'` to create one.
*   `MAIL_USERNAME`, `MAIL_PASSWORD`, `MAIL_DEFAULT_SENDER`: Fill in your email provider credentials. For Gmail, you will likely need to generate an "App Password".

**c. Review `config.json`**
This file defines the paths for your ETL process. The default structure is created for you, but you can change it if needed. You can also edit this file later from the Admin dashboard.

### **4. Database Setup**

The application uses Flask-Migrate to manage database schema changes.

```bash
# (Make sure your virtual environment is active)

# Initialize the database (creates the 'app.db' file and migration folder)
# If you get an error that the directory already exists, you can skip this command.
flask db init

# Create the first migration (captures the User, Role, Otp tables)
flask db migrate -m "Initial migration with new models"

# Apply the migration to the database
flask db upgrade
```

### **5. Running the Application**

The application requires three main components to be running: the Redis server, the RQ worker, and the Flask web server.

**a. Start Redis**
Use Docker Compose to start a Redis container in the background.

```bash
docker-compose up -d
```
*To stop it later, run `docker-compose down`.*

**b. Start the RQ Worker**
The worker process listens for jobs on the Redis queue. Open a **new terminal window**, activate the virtual environment, and run:

```bash
# (Activate the virtual environment first: source venv/bin/activate)
python worker.py
```
This terminal will be busy listening for jobs. Keep it open to see the output from background tasks.

**c. Start the Flask Web Server**
Open a **third terminal window**, activate the virtual environment, and run:

```bash
# (Activate the virtual environment first: source venv/bin/activate)
flask run
```
The application will be available at `http://127.0.0.1:5000`.

### **6. First-Time Application Setup**

**a. Create Database Roles**
Before you can register users, you need to populate the `Role` table. With the Flask app running, open your web browser and go to this special URL:
**http://127.0.0.1:5000/public/setup/roles**

You should see a message confirming the roles were created.

**b. Register Your First User(s)**
- **User:** Navigate to **http://127.0.0.1:5000/public/register** and create a user account. The email **must** end in `@ntplc.co.th`.
- **Admin:** There is no public registration for admins. You must create an admin manually.

**c. Make a User an Admin**
To create an admin account, first register a normal user (e.g., `admin@ntplc.co.th`). Then, use the Flask shell to assign the 'admin' role.

```bash
# In a new terminal with the venv activated
flask shell
```

In the shell, run the following commands, replacing the email with your admin user's email.

```python
from app.models import User, Role
from app import db

# Find the user you want to make an admin
user = User.query.filter_by(email='admin@ntplc.co.th').first()

# Find the 'admin' role
admin_role = Role.query.filter_by(name='admin').first()

if user and admin_role:
    # Add the admin role to the user
    user.roles.append(admin_role)
    db.session.commit()
    print(f"User {user.email} is now an admin.")
else:
    print("User or admin role not found.")

# Exit the shell
exit()
```

### **7. Using the Application**

1.  **Login:** Go to `http://127.0.0.1:5000`. Enter your credentials. You will be sent an OTP code to your email.
2.  **Verify OTP:** Enter the 6-digit code to complete the login.
3.  **Admin Dashboard:** If you are an admin, you will be redirected here. You can:
    *   Run an ETL job by providing a year and month.
    *   Monitor running and failed jobs.
    *   View the latest log files.
    *   Navigate to the Config page to edit `config.json` live.
    *   Navigate to the Logs page to see all log files.
4.  **User Dashboard:** If you are a standard user, you will see a list of available reports to download. These reports are generated by the admin's ETL jobs.