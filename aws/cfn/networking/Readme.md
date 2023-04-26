##Architecture Guide

Create a CFN s3 bucket before running any templates to contain all artifacts for CloudFormation

```
aws s3 mk s3://cfn-project-artifact
export CFN_BUCKET="cfn-project-artifact"
gp env CFN_BUCKET="cfn-project-artifact"
```