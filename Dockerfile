# Use the official Python image as the base image
FROM python:3.10-alpine

# Add Metadata
LABEL maintainer="Marcus Adebayo <marcus.adebayo8@gamil.com>"
LABEL description="A Discord chatbot that uses the OpenAI GPT-3.5 model for natural language processing."

# Set the working directory in the container
WORKDIR /app

# Copy the application files into the container
COPY . .

# Set the environment variables
ENV DISCORD_API_KEY=your_discord_api_key_here
ENV OPENAI_API_KEY=your_openai_api_key_here

# Install the required packages
RUN apk add --no-cache --virtual .build-deps gcc musl-dev \
    && pip install --no-cache-dir -r requirements.txt \
    && apk del .build-deps \
    && addgroup -S appgroup \
    && adduser -S appuser -G appgroup \
    && chown -R appuser:appgroup /app

# Switch to non-root user
USER appuser

# Start the application
CMD ["python", "main.py"]

