# EC2 QuickLook
A tool that help you to quickly query EC2 instance information, including: configuration, specifications, features and monthly usage costs for reference. 

## What is this project?
This project is my practice of using aws chalice for python development.  It contains backend API and a simple frontend page, and integrates swagger ui to visualize the API's resources.
You can deploy it to AWS cloud environment to run with one command when you complete the code development of all functions and interfaces, . No server, container, storage, etc. resources are needed for deployment.
It's that simple! 

<br>

## AWS Chalice

[AWS Chalice](https://aws.github.io/chalice/) is a micoservice framework for writing serverless appications in python. User can quickly create and deploy applications to AWS environment.

- [AWS Chalice Tutorial & Documentation](https://aws.github.io/chalice/tutorials/index.html)

<br>

## Prerequisite

- [Visual Studio Code](#)
- [Python](https://www.python.org/downloads/release/python-381/) >= 3.8.1
- [AWS Credential](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-files.html)

<br>

## Install

Clone Git repository to local and navigate to the project folder

```bash

❯ git clone https://github.com/aleck31/ec2-quicklook.git

❯ cd ec2-quicklook

```

Setup Python Virtual Environment

```bash

❯ python -m venv .venv

```

Activate Python Virtual Environment

```bash

# Window
❯ .venv/Scripts/Activate.ps1

# Linux/Mac
$ source .venv/bin/Activate

```

Install Required Python Library

```bash

❯ pip install -r requirements.txt

```
Create Resources
```bash

❯ python create-resources.py

```
Create Users for Auth
```bash

❯ python users.py --add-user

 Username: <demo_user>
 Password: <your_passwd>

```
Run Locally for Experience [option]

```bash

❯ chalice local 

```
 
Deploy To AWS

```bash

❯ chalice deploy 

Updating lambda function: ec2-quicklook-dev
Updating rest API
Resources deployed:
  - Lambda ARN: arn:aws:lambda:us-east-1::function:ec2-quicklook-dev
  - Rest API URL: https://...execute-api.us-east-1.amazonaws.com/api/

```

You should see a familiar [Swagger UI](https://swagger.io/tools/swagger-ui/) at the docs endpoint like this:  
https://...execute-api.us-east-1.amazonaws.com/api/docs

<br>

## Environment Setup

### Log Level

Log level is controlled by `ENV_LOG_LEVEL` environment variables. `.chalice\config.json`

- CRITICAL
- ERROR
- WARNING
- INFO
- DEBUG
- NOTSET

- Reference: [logging level](https://docs.python.org/3/library/logging.html#levels)

<br>

### Custom IAM Role Policy

You can customize the IAM role policy with your project.

- [AWS Chalice Document](https://aws.github.io/chalice/topics/configfile#iam-policy-file)
- [AWS IAM Policy](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies.html)
