FROM ghcr.io/open-webui/pipelines:main
LABEL authors="eresque"

COPY requirements.txt ./extra_requirements.txt
RUN pip install -r ./extra_requirements.txt

COPY generation.py ./pipelines

ENTRYPOINT [ "bash", "start.sh" ]
