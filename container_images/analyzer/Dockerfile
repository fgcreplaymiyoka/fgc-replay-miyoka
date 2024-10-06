# Use the official Python image as the base image
FROM python:3.10.13

RUN apt-get update && apt-get install ffmpeg libsm6 libxext6  -y

# No virtual env creation
# ref https://stackoverflow.com/questions/53835198/integrating-python-poetry-with-docker
ENV POETRY_VIRTUALENVS_CREATE=false

# Set the working directory inside the container
WORKDIR /app

# Copy the rest of the project files to the container
COPY . /app

# Install Poetry
RUN pip install poetry

# Install project dependencies
RUN poetry install

# Set the entrypoint command to run the frame-analyzer.py script
CMD ["make", "analyze"]