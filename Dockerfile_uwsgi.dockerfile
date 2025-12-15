# Base OS with Python and tools
FROM debian:latest
# Metadata: Wenjing Ma
LABEL MAINTAINER="mawenjing1993@gmail.com"

# Update OS
RUN apt-get update -y

# Install Python + build tools (keep as-is, just drop Apache)
RUN apt-get update && apt-get install -y \
    build-essential \
    python3 \
    python3-dev \
    python3-pip \
    vim \
 && apt-get clean \
 && apt-get autoremove \
 && rm -rf /var/lib/apt/lists/*

# Install uwsgi
RUN pip3 install --no-cache-dir --break-system-packages uwsgi

# App deps
COPY ./requirements.txt /BARTweb/requirements.txt
RUN pip3 install --break-system-packages -r /BARTweb/requirements.txt

# App code
RUN mkdir -p /BARTweb
COPY . /BARTweb/

# Prepare a writable usercase root (same fix that solved the 500)
RUN mkdir -p /BARTweb/usercase \
 && chown -R www-data:www-data /BARTweb/usercase \
 && chmod -R 775 /BARTweb/usercase

# Logs
RUN mkdir -p /log /BARTweb/usercase/log \
 && touch /log/bartweb.log /BARTweb/usercase/log/bartweb.log \
 && chown -R www-data:www-data /log /BARTweb/usercase/log \
 && chmod -R 775 /BARTweb/usercase/log

WORKDIR /BARTweb/

# Root stuff
# Create a non-root user and group called "app"
RUN groupadd -g 1001 app && useradd -u 1001 -g app -m app
# Give ownersip of app + log dirs to user
RUN chown -R app:app /BARTweb /log
# Switch to new user
USER app

# Flask default port
EXPOSE 5000

# Run Flask app (app.py already has host='0.0.0.0')
CMD ["uwsgi", "--ini", "uwsgi.ini"]
