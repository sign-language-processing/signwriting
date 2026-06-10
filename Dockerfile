# ---- Build stage: compile flite and install python dependencies ----
FROM python:3.12-slim AS builder

RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential git ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Build flite to get lex_lookup, used by epitran for English IPA
WORKDIR /build
RUN git clone --depth 1 https://github.com/festvox/flite.git
RUN cd flite && ./configure && make
RUN cd flite/testsuite && make lex_lookup

# Install everything into a venv so the runtime stage can copy it as-is
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN python -m venv $VIRTUAL_ENV

WORKDIR /app
COPY . .
RUN pip install --no-cache-dir ".[mouthing,server]"

# ---- Runtime stage ----
FROM python:3.12-slim

# Allow statements and log messages to immediately appear in the native logs
ENV PYTHONUNBUFFERED=True

COPY --from=builder /build/flite/testsuite/lex_lookup /usr/local/bin/lex_lookup
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Download epitran data at build time and verify lex_lookup works end-to-end
RUN python -c "import epitran; print(epitran.Epitran('eng-Latn').transliterate('hello'))"

# Timeout is set to 0 to disable the timeouts of the workers to allow Cloud Run to handle instance scaling.
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 signwriting.server:app
