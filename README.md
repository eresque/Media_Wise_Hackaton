# Media_Wise_Hackaton
# Project structure 
```commandline
.
├── docker-compose.yml
├── OpenWebUI
│   └── pipelines
│       ├── Dockerfile
│       ├── generation.py
│    └── requirements.txt
└── README.md

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