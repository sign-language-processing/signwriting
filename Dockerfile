FROM python:3.11-slim

# Allow statements and log messages to immediately appear in the native logs
ENV PYTHONUNBUFFERED True

## Install system dependencies
RUN apt-get update && apt-get install -y build-essential git

# Setup local workdir and dependencies
WORKDIR /app

# Install flite to support mouthing
RUN git clone https://github.com/festvox/flite.git
RUN cd flite && ./configure && make && make install
RUN cd flite/testsuite && make lex_lookup && cp lex_lookup /usr/local/bin

# Downloads NLTK data
RUN pip install epitran
RUN python -c "import epitran"

# Copy local code to the container image.
COPY . .

# Install python dependencies.
RUN pip install --no-cache-dir ".[dev,mouthing,server]"

# Timeout is set to 0 to disable the timeouts of the workers to allow Cloud Run to handle instance scaling.
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 signwriting.server:app
