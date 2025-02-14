# Use the official Python image as the base image
FROM python:3.10.13

RUN apt-get update && apt-get install ffmpeg libsm6 libxext6 curl -y

# Install Node.js
ENV NODE_VERSION=20.8.0
RUN curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash
ENV NVM_DIR=/root/.nvm
RUN . "$NVM_DIR/nvm.sh" && nvm install ${NODE_VERSION}
RUN . "$NVM_DIR/nvm.sh" && nvm use v${NODE_VERSION}
RUN . "$NVM_DIR/nvm.sh" && nvm alias default v${NODE_VERSION}
ENV PATH="/root/.nvm/versions/node/v${NODE_VERSION}/bin/:${PATH}"
RUN node --version
RUN npm --version

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
RUN poetry install --with frontend

# Build the frontend of the streamlit custom component
RUN cd miyoka/sf6/video_component/frontend && \
    npm install && \
    npm run build

# Default port of cloud run
EXPOSE 8080

# Set the entrypoint command to run the frame-analyzer.py script
CMD ["make", "viewer"]