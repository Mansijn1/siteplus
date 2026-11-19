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

# LIGHTHOUSE_CHROME_PATH is intentionally NOT set here — config.py asks Playwright directly for
# its installed Chromium's executable_path at startup, so Lighthouse always reuses the exact
# browser this image's pinned Playwright version actually installed, rather than a hardcoded
# path/revision guess that could drift or be wrong for this platform.

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
