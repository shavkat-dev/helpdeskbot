# Dockerfile

# 1. Base Image
FROM python:3.9-slim

# 2. Apply OS security patches
# This is a critical security step. It updates the package lists and installs
# the latest security patches for the underlying OS packages.
RUN apt-get update && apt-get upgrade -y && rm -rf /var/lib/apt/lists/*

# 3. Install OS-level dependencies for localization
# The 'gettext' package provides the 'msgfmt' command needed to compile .po files.
RUN apt-get install -y gettext

# 4. Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy the application code
COPY . .

# 6. Compile translation files
RUN msgfmt locale/pt_BR/LC_MESSAGES/pt_BR.po -o locale/pt_BR/LC_MESSAGES/helpdeskbot.mo

# 7. Command to run the application
CMD ["python", "-c", "from main import updater; updater.start_polling()"]