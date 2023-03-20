# Use the official Python image as the base image
FROM python:3.10-alpine

# Set the working directory in the container
WORKDIR /app

# Copy the application files into the container
COPY . .

# Set the environment variables
ENV DISCORD_API_KEY=your_discord_api_key_here
ENV OPENAI_API_KEY=your_openai_api_key_here

# Install the required packages
RUN apk add --no-cache gcc musl-dev && \
    pip install --no-cache-dir -r requirements.txt && \
    apk del gcc musl-dev

# Start the application
CMD python main.py