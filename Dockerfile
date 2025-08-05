FROM python:3.10-slim
WORKDIR /app

# Install poetry first
RUN pip install poetry

# Copy all project files
COPY . .

# Configure poetry and install everything.
# This will create the `coe-cli` executable in a system path.
RUN poetry config virtualenvs.create false && \
    poetry install --without dev

# The command should now be available in the PATH
CMD ["coe-cli"]

