# EC2 QuickLook
A web tool that help you to quickly query EC2 instance information, including: configuration, specifications, features and monthly on-demand price for reference. 

<br>

## What is this project?
This is an example project of using aws chalice for python development.  It contains a simple frontend page, backend API, and integrates **swagger ui** to visualize the API's resources. 
You can deploy it to AWS cloud with one command when you complete the code development of all functions and interfaces. No server, container, storage etc. resources needed for deployment. 
Pretty simple! 

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

❯ python -m venv .env

```

Activate Python Virtual Environment

```bash
# Linux/Mac
$ source .venv/bin/Activate

# Window
❯ .venv/Scripts/Activate.ps1
```

Install Required Python Library

```bash

❯ pip install -r requirements.txt

```
Create Resources （default --stage dev）
```bash

❯ python create-resources.py

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

## Troubleshooting

### Access denied
If you got an "AccessDeniedException" error, pls ensure that the correct permissions are configured for lambda's service role. You can refer to example/**role_policy.json** to update the lambda role permissions.

### Query in AWS China Region
If you encounter an error when querying AWS China region, please make sure you have an AWS China account, and save the credentials in secrets manager, then replace the value of **SECRET_NAME** in the config.json file.



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
