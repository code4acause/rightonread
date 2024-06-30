# rightonread

## Installation Instructions:

```pip install -r requirements.txt```

Write the `.streamlit/secrets.toml` file with the following content:

```
mongo_username = "..."
mongo_password = "..."
google_key = "..."
```

Then, to run the app:

```streamlit run main.py```

## Development with Docker
Run the following commands to build the dev docker image and run the container that use local files throughout development process:
```
podman build -t read .
podman run -p 8501:8501 --name read -v %cd%:/home/streamlit read
podman start read -a
podman exec -it read bash
podman run -p 8501:8501 --rm -v %cd%:/home/streamlit read pages/profile.py
```