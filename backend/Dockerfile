# Base image ships Python + Chromium/Firefox/WebKit + every OS-level dependency Playwright
# needs already installed and version-matched to playwright==1.49.1 in requirements.txt — this
# is why the backend doesn't need a separate `playwright install --with-deps` step here. If you
# bump the playwright version in requirements.txt, bump this tag to match.
FROM mcr.microsoft.com/playwright/python:v1.49.1-noble

# Lighthouse runs as a Node CLI (via `npx lighthouse`) even though the rest of the backend is
# Python — this is the one place the two runtimes have to coexist in the same container.
#
# Installed from the official prebuilt tarball rather than apt + nodesource's GPG-keyed repo:
# that path pulls in gnupg/dirmngr and their dependency chain, which failed a real build here
# when the build network couldn't reach archive.ubuntu.com over IPv6, leaving apt with broken
# package lists it couldn't resolve. Fetching one HTTPS tarball needs only curl and tar, both
# already present, and sidesteps apt entirely for this step.
ENV NODE_VERSION=20.18.1
RUN curl -fsSL "https://nodejs.org/dist/v${NODE_VERSION}/node-v${NODE_VERSION}-linux-x64.tar.gz" -o /tmp/node.tar.gz \
    && tar -xzf /tmp/node.tar.gz -C /usr/local --strip-components=1 \
    && rm /tmp/node.tar.gz \
    && node --version && npm --version

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN mkdir -p storage/screenshots storage/lighthouse

# LIGHTHOUSE_CHROME_PATH is resolved here, in a plain shell script run before uvicorn starts,
# rather than inside config.py's own `sync_playwright()` call at Python import time: that
# in-process call returned None on the live container (silently swallowed by its try/except),
# because it's racing uvicorn's own event loop startup — Playwright's sync API refuses to run
# from a thread that already has (or is about to have) an asyncio loop. A separate shell
# process has no event loop at all, so the same Playwright query is unambiguous here.
RUN cat <<'EOF' > /app/entrypoint.sh
#!/bin/sh
set -e
if [ -z "$LIGHTHOUSE_CHROME_PATH" ]; then
    export LIGHTHOUSE_CHROME_PATH="$(python -c 'from playwright.sync_api import sync_playwright; p = sync_playwright().start(); print(p.chromium.executable_path)')"
fi
echo "Resolved LIGHTHOUSE_CHROME_PATH=$LIGHTHOUSE_CHROME_PATH"
exec uvicorn main:app --host 0.0.0.0 --port 8000
EOF
RUN chmod +x /app/entrypoint.sh

EXPOSE 8000

CMD ["/app/entrypoint.sh"]
