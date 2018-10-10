# Serverless pipeline in AWS with sceptre
Sample CI/CD pipeline for a serverless infrastructure in AWS.

## Repo structure
### Sceptre
- **`config/`**: Sceptre configuration files for environments (all the config.yml files) and CloudFormation stacks (the rest of the YAMLs).
  - **`config/<dir>/`**: Each dir inside config represents an environment, there's just one in this repo (dev).
- **`hooks/ | resolvers/`**: Sceptre _plugin_ directories. In this project they only contain helpers to upload lambdas to S3 before launching CloudFormation stacks.
- **`templates/`**: CloudFormation templates. Besides mundane JSON/YAML CloudFormation templates, Sceptre supports templating with Jinja2 and Troposphere.
### Code
- **`dependencies/`**: Project dependencies (Sceptre, Troposphere, ...) and test dependencies for lambda functions, regardless of the language. It's probably a good idea to have same test dependencies for all lambdas.
- **`script/`**: Scripts for testing and CI/CD automation. Based on [Scripts to rule them all](https://github.com/github/scripts-to-rule-them-all).
- **`src/`**: The actual source of the project.
  - **`src/swagger.cloudformation.yaml`**: The swagger file for the API Gateway. It's actually a template since it includes several _!Ref_ to CloudFormation resources.
  - **`src/<lambda>/`**: The lambda function code. Each lambda has to have a _Makefile_ whose default target has to generate a `dist/` directory with the code that will be bundled into a .zip and uploaded to S3.
- **`tools/`**: Helper scripts and config files.

## Notice
Botocore will issue lots of DeprecationWarnings when using python 3.7, it's not Sceptre's fault.
A PR it's on its way to address the issue: https://github.com/boto/botocore/pull/1577
Workaround:
`sed -i 's/value.getchildren()/list(value)/' .venv/lib/python3.7/site-packages/botocore/parsers.py`
