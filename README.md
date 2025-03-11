# EC2 QuickLook

A web tool that helps you quickly query EC2 instance information, including configuration, specifications, features, and monthly on-demand price for reference.

## Features

- 🔍 Query EC2 instance details and OD pricing
- 💾 EBS volume OD pricing
- 🌐 Support for both AWS Global and China regions
- 📊 Detailed instance specifications
- 🚀 Serverless deployment with AWS Chalice
- 📝 Swagger UI API documentation

## What is this project?

This is a demonstration project for [AWS Chalice](https://aws.github.io/chalice/), a microservice framework for writing serverless applications in Python. The project features a modern Vue.js frontend with Bootstrap-Vue components, RESTful backend APIs, and integrated Swagger UI for API documentation.

You can deploy it to the AWS cloud with a single command. No servers, containers, or storage resources are required for deployment.

## Architecture

- **Infrastructure**: AWS Lambda + API Gateway (managed by Chalice)
- **Storage**: Amazon DynamoDB
- **Frontend**: Vue.js with Bootstrap-Vue components
- **Backend**: Python with AWS Chalice framework
- **API Documentation**: Swagger UI

## File Structure

ec2-quicklook/
├── app.py                 # Main application entry point
├── chalicelib/
│   ├── config.py         # Configuration management
│   ├── sdk.py            # AWS SDK integration
│   ├── utils.py          # Utility functions
│   ├── models.py         # Data models
│   ├── product/          # Product-related functionality
│   ├── swagger/          # Swagger UI integration
│   ├── webui/             # Web interface
│   └── static/          # Static assets
└── tests/               # Test files

## Prerequisites

- [Python](https://www.python.org/downloads/release/python-3100/) >= 3.10
- [AWS Chalice](https://aws.github.io/chalice/)
- [AWS Credentials](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-files.html) (with appropriate permissions)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/aleck31/ec2-quicklook.git
cd ec2-quicklook
```

2. Set up Python virtual environment:
```bash
python -m venv .venv

# Linux/Mac
source .venv/bin/activate

# Windows
.venv/Scripts/Activate.ps1
```

3. Install required dependencies:
```bash
pip install -r requirements.txt
```

4. Create required AWS resources:
```bash
# Create resources (default --stage dev)
python create-resources.py
```

## Local Development

1. Run the application locally:
```bash
chalice local
```

2. Access the application:
- Main application: http://127.0.0.1:8000
- API documentation: http://127.0.0.1:8000/api/docs

## Deployment

Deploy to AWS:
```bash
chalice deploy

# Example output:
Updating lambda function: ec2-quicklook-dev
Updating rest API
Resources deployed:
  - Lambda ARN: arn:aws:lambda:us-east-1::function:ec2-quicklook-dev
  - Rest API URL: https://...execute-api.us-east-1.amazonaws.com/api/
```

After deployment, you can access:
- Main application: https://...execute-api.us-east-1.amazonaws.com/api/
- API documentation: https://...execute-api.us-east-1.amazonaws.com/api/docs

## Environment Configuration

### Log Level

Log level is controlled by `ENV_LOG_LEVEL` environment variable in `.chalice/config.json`:

- CRITICAL
- ERROR
- WARNING
- INFO
- DEBUG
- NOTSET

Reference: [Python logging levels](https://docs.python.org/3/library/logging.html#levels)

### IAM Role Policy

You can customize the IAM role policy for your project:

- [AWS Chalice IAM Documentation](https://aws.github.io/chalice/topics/configfile#iam-policy-file)
- [AWS IAM Policy Documentation](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies.html)

## Troubleshooting

### Access Denied
If you encounter an "AccessDeniedException", ensure that the correct permissions are configured for the Lambda service role. Refer to `example/role_policy.json` to update the Lambda role permissions.

### AWS China Region
For AWS China region queries:
1. Ensure you have an AWS China account
2. Save the credentials in AWS Secrets Manager
3. Update the `SECRET_NAME` in `config.json`

### Local Development
Common issues and solutions:

1. **DynamoDB Connection**: Ensure your AWS credentials have DynamoDB access permissions
2. **API Gateway**: Local development uses a mock API Gateway, some features might behave differently
3. **Environment Variables**: Check `.chalice/config.json` for correct environment variable configuration

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [AWS Chalice Tutorial](https://aws.github.io/chalice/tutorials/index.html) - Python Serverless Framework
- [AWS Pricing API](https://aws.amazon.com/aws-cost-management/aws-price-list-api/) - EC2 Pricing Information
- [Bootstrap-Vue](https://bootstrap-vue.org/) - Vue.js Implementation of Bootstrap
- [Swagger UI](https://swagger.io/tools/swagger-ui/) - API Documentation
