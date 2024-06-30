FROM python:3.10-slim
LABEL maintainer="Darren Weng"

# Copy the requirements and install them
RUN mkdir -p /home/streamlit
WORKDIR /home/streamlit

COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy the rest of the files
# COPY . /home/streamlit

ENTRYPOINT [ "streamlit", "run"]
CMD ["main.py"]