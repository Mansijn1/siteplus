# Base image ships Python + Chromium/Firefox/WebKit + every OS-level dependency Playwright
# needs already installed and version-matched to playwright==1.49.1 in requirements.txt — this
# is why the backend doesn't need a separate `playwright install --with-deps` step here. If you
# bump the playwright version in requirements.txt, bump this tag to match.
FROM mcr.microsoft.com/playwright/python:v1.49.1-noble

# Lighthouse runs as a Node CLI (via `npx lighthouse`) even though the rest of the backend is
# Python — this is the one place the two runtimes have to coexist in the same container.
RUN apt-get update && apt-get install -y --no-install-recommends curl gnupg \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN mkdir -p storage/screenshots storage/lighthouse

# Point Lighthouse at the Chromium this base image already shipped, instead of letting
# chrome-launcher search for (or try to download) its own copy.
ENV LIGHTHOUSE_CHROME_PATH=/ms-playwright/chromium-1148/chrome-linux/chrome

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
