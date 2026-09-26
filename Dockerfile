FROM python:3.11-slim

LABEL maintainer="Team BWU INCURSION 1.0 <soumyadeepmagnusx@users.noreply.github.com>"
LABEL org.opencontainers.image.title="RAINSHIELD-AI v6.0 (SIH26071 - Ministry of Earth Sciences)"
LABEL org.opencontainers.image.description="AI/ML-Based Integrated Heavy Rainfall Early Warning & 2D Inundation Prediction System"

WORKDIR /app

COPY . /app

# Verify ML artifacts & SQLite database on container build
RUN python -m ml_pipeline.train_pipeline

EXPOSE 8090

ENV PORT=8090
ENV PYTHONUNBUFFERED=1

CMD ["python", "server.py"]
