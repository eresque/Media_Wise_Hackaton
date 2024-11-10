# Media_Wise_Hackaton
# Project structure 
```commandline
.
├── benchmarking
│   ├── data
│   │   └── benchmarking_data.csv
│   └── evaluate_pipe.py
├── embedder
│   ├── Dockerfile
│   ├── inference.py
│   └── requirements.txt
├── llm
│   ├── Dockerfile
│   ├── inference.py
│   ├── prompts.py
│   ├── __pycache__
│   │   ├── inference.cpython-311.pyc
│   │   └── prompts.cpython-310.pyc
│   └── requirements.txt
├── OpenWebUI
│   └── pipelines
│       ├── generation.py
│       ├── insertion.py
│       └── requirements.txt
├── reranker
│   ├── Dockerfile
│   ├── inference.py
│   └── requirements.txt
├── README.md
├── docker-compose.yml
└── Dockerfile-openwebui-pipeline

```
# Project launch 
## Requirements
`Python version >= 3.11` </br>
`Docker engine` </br>
`.env` file in project root with such structure:
```commandline
IAM_TOKEN=<your_personal_iam_token>
```
## Launch commands 
```commandline
docker compose up --build 
```

## Usage 
By now the project is up and running. To start using it go to `http://localhsot:3057`