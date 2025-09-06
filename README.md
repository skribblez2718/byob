# BYOB (Bring Your Own Blog)

A modern, a Flask-based blog/portfolio application with admin dashboard, multi-factor authentication, and customizable themes.

## Features

- **Secure Authentication**: Multi-factor authentication (MFA) with TOTP support
- **Admin Dashboard**: Complete content management system for posts, categories, and projects
- **Rate Limiting**: Some semblance of protection against brute force attacks
- **Responsive Design**: Mobile-friendly with customizable color schemes
- **SEO Friendly**: Clean URLs and proper meta tags
- **Database Migrations**: Alembic integration for schema management
- **Security Headers**: CSP, CSRF protection, and secure session handling

## Requirements

- Python 3.8+
- PostgreSQL 12+
- Node.js (for frontend dependencies, optional)

## Installation

### Option 1: Using Virtual Environment (venv)

```bash
# Clone the repository
git clone <repository-url>
cd byob

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Option 2: Using UV (Recommended for speed)

```bash
# Install UV if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone the repository
git clone <repository-url>
cd byob

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -r requirements.txt
```

### Option 3: Using Poetry

```bash
# Install Poetry if not already installed
curl -sSL https://install.python-poetry.org | python3 -

# Clone the repository
git clone <repository-url>
cd byob

# Install dependencies
poetry install
poetry shell
```

## Database Setup

### 1. Install PostgreSQL

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
```

**macOS:**
```bash
brew install postgresql
brew services start postgresql
```

**Windows:**
Download and install from [PostgreSQL official website](https://www.postgresql.org/download/windows/)

### 2. Configure Database

1. **Edit the init_db.sql file:**
   ```bash
   cp init_db.sql init_db_local.sql
   ```

2. **Replace the placeholder password:**
   Open `init_db_local.sql` and replace `<STRONG_PASSWORD_HERE>` with a secure password:
   ```sql
   CREATE ROLE blog LOGIN PASSWORD 'your_secure_password_here';
   ```

3. **Run the database initialization script:**
   ```bash
   # Connect as postgres superuser
   sudo -u postgres psql -f init_db_local.sql
   
   # Or if you have postgres user access:
   psql -U postgres -f init_db_local.sql
   ```

   This script will:
   - Create a `blog` database role with minimal privileges
   - Create a `blog` database
   - Set up proper schema permissions
   - Configure search paths

## Environment Configuration

### 1. Create Environment File

Copy the example environment file and customize it:

```bash
cp .env.example .env
```

### 2. Configure Environment Variables

Edit the `.env` file with your settings:

```bash
# Flask Configuration
FLASK_ENV=production  # or 'development' for dev mode
SESSION_LIFETIME_MINUTES=480
MAX_CONTENT_LENGTH=5242880

# Database Configuration
DATABASE_URL=postgresql+psycopg2://blog:change-this-very-strong-password@localhost:5432/blog

# Rate Limiting (optional overrides)
RATELIMIT_DEFAULT=100 per minute
RATELIMIT_STORAGE_URI=memory://

# Caching
CACHE_TYPE=SimpleCache

# Misc.
SITE_NAME="Site Name"
```

### 3. Generate Secret Keys

Generate secure secret keys:

```bash
# Generate SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(32))"

```

## Database Migration

Initialize and run database migrations:

```bash
# Initialize migration repository (first time only)
flask db init

# Apply migrations
flask db upgrade

# Create initial migration
flask db migrate -m "Initial migration"
```

## Create Admin User

Create your first admin user:

```bash
# Run the create admin command
flask create-admin

# Follow the prompts to enter:
# - Username
# - Password (with confirmation)
```

## Running the Application

### Development Mode

```bash
# Using Flask development server
flask run

# Or using Python directly
python run.py
```

The application will be available at `http://localhost:5000`

### Production Mode with Gunicorn

Install gunicorn with threading support:

```bash
pip install gunicorn[gthread]
```

Run using the included configuration file:

```bash
gunicorn -c gunicorn.conf.py wsgi:application
```

The `gunicorn.conf.py` file is included in the project root with production-ready settings optimized for HTTP/2 support and performance.

## Systemd Service Setup

### 1. Create Service User

```bash
# Create a dedicated system user with minimal privileges
sudo useradd --system \
             --no-create-home \
             --shell /usr/sbin/nologin \
             --home-dir /opt/byob \
             --comment "BYOB Blog Application" \
             byob

# Create application directory with proper ownership
sudo mkdir -p /opt/byob
sudo chown byob:byob /opt/byob
sudo chmod 755 /opt/byob

# Create log directory with proper permissions
sudo mkdir -p /var/log/byob
sudo chmod 755 /var/log/byob
sudo touch /var/log/byob/error.log /var/log/byob/access.log
sudo chmod 660 /var/log/byob/access.log
sudo chmod 660 /var/log/byob/error.log
sudo chown -R byob:byob /var/log/byob
```

### 2. Setup Application Directory

```bash
# Copy application files
sudo cp -r /path/to/your/byob/* /opt/byob/
sudo chown -R byob:byob /opt/byob
```

### 3. Create Systemd Service File

Create `/etc/systemd/system/byob.service`:

```ini
[Unit]
Description=BYOB (Bring Your Own Blog) Flask Application
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=byob
Group=byob
WorkingDirectory=/home/byob/byob

# Make sure processes see the right HOME and can find basic binaries
Environment=HOME=/home/byob
Environment="PATH=/home/byob/byob/venv/bin:/usr/bin:/bin"

# If you keep a dotenv-style file, point to it in /home
EnvironmentFile=/home/byob/byob/.env

ExecStart=/home/byob/byob/venv/bin/gunicorn -c /home/byob/byob/gunicorn.conf.py wsgi:app
ExecReload=/bin/kill -s HUP $MAINPID
Restart=on-failure
RestartSec=10
KillMode=mixed
TimeoutStopSec=5

# Hardening compatible with /home
ProtectSystem=strict
ProtectHome=read-only
ReadWritePaths=/home/byob/byob /var/log/byob
PrivateTmp=true
NoNewPrivileges=true
UMask=027

[Install]
WantedBy=multi-user.target
```

### 4. Enable and Start Service

```bash
# Reload systemd configuration
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable byob

# Start the service
sudo systemctl start byob

# Check service status
sudo systemctl status byob

# View logs
sudo journalctl -u byob -f
```

### 5. Service Management Commands

```bash
# Start service
sudo systemctl start byob

# Stop service
sudo systemctl stop byob

# Restart service
sudo systemctl restart byob

# Reload service (graceful restart)
sudo systemctl reload byob

# Check status
sudo systemctl status byob

# View logs
sudo journalctl -u byob -n 50  # Last 50 lines
sudo journalctl -u byob -f     # Follow logs
```

## Reverse Proxy Setup (Nginx)

For production deployment with HTTP/2, set up nginx as a reverse proxy:

### 1. Install Nginx

```bash
sudo apt install nginx  # Ubuntu/Debian
# or
brew install nginx      # macOS
```

### 2. Configure Nginx

Create `/etc/nginx/sites-available/byob`:

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    # SSL Configuration
    ssl_certificate /path/to/your/certificate.crt;
    ssl_certificate_key /path/to/your/private.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    # Security Headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload";

    # Static files
    location /static/ {
        alias /opt/byob/app/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Proxy to Gunicorn
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
        proxy_buffering off;
    }
}
```

### 3. Enable Site

```bash
# Enable the site
sudo ln -s /etc/nginx/sites-available/byob /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Restart nginx
sudo systemctl restart nginx
```

## Development

### Running Tests

```bash
# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=app tests/

# Run specific test file
python -m pytest tests/test_auth.py
```

### Code Quality

```bash
# Format code with black
black app/ tests/

# Lint with flake8
flake8 app/ tests/

# Type checking with mypy
mypy app/
```

### Database Operations

```bash
# Create new migration
flask db migrate -m "Description of changes"

# Apply migrations
flask db upgrade

# Downgrade migration
flask db downgrade

# Show migration history
flask db history
```

## Customization

### Theme Customization

The application uses CSS custom properties for easy theme customization. Edit `app/static/css/main.css`:

```css
:root {
  /* Change these values to customize the color scheme */
  --accent: #f59e0b;        /* Primary accent color */
  --green: #22c55e;         /* Success/positive actions */
  --red: #ef4444;           /* Errors/negative actions */
  --text: #ffffff;          /* Primary text color */
  --background: #0a0a0a;    /* Main background */
  /* ... more variables available */
}
```