# Preview + Upload servers — lightweight Python image
FROM python:3.11-slim

WORKDIR /app

COPY preview_server.py upload_server.py ./

# No pip dependencies needed — pure stdlib

EXPOSE 8081 8082

# Default: preview server. Override CMD in compose for upload.
CMD ["python3", "preview_server.py"]
