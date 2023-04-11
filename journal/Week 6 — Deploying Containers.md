# Week 6 — Deploying Containers

#### Business Use-case

Fargate will be used initially since its Serverless Containers so we don't have to manage the underlying compute. It’s a good migration path to Kubernetes, you can run Fargate on Kubernetes/EKS.



### 1. Implementing health checks for db and Flask

##### Context:
  - In this [commit](
https://github.com/imaginarydumpling/aws-bootcamp-cruddur-2023-clone/commit/f6ccd86e06ae32a259e247ad7c5d116d2023d1f2), we added a connection check for our production database. Running the **test.py** will verify if RDS is up and running.

  - While in this [commit](https://github.com/imaginarydumpling/aws-bootcamp-cruddur-2023-clone/commit/f6ccd86e06ae32a259e247ad7c5d116d2023d1f2#diff-01d7ad6d634a3ec30374d54f33e9e024f562ff3eca15fdea99bb1119f41de4be) we added a health check for our backend-flask to verify if its also up and running. This will be used later as health-checks for our ECS backend-flask service.

  - Results should show a **Connection Successful** when running the backend-flask/health-check


### 2. Create task definitions

  - In this [commit](https://github.com/imaginarydumpling/aws-bootcamp-cruddur-2023-clone/commit/4217c23968e24e59f60bbca40d4530a290dc2051), We created new policies and added them to our IAM permissions, this will allow us the necessary permissions to use ECS in conjunction with Systems Manager parameters.

  - We will also create task definitions for our backend-flask and frontend-react-js located in this [commit](https://github.com/imaginarydumpling/aws-bootcamp-cruddur-2023-clone/commit/4217c23968e24e59f60bbca40d4530a290dc2051#diff-fce4cbfaaa6ae500dea2961ebd2e8395ff961a7a764b1cebc1f11325d50a2866). This will be used later to register our task-definitions in our cluster called "cruddur" which is created in ECS.

  - We will also create a ECS cluster using this commands       
    
    ```
	aws ecs create-cluster \
--cluster-name cruddur \
--service-connect-defaults namespace=cruddur
    ```

  - Results should show a created cluster in AWS ECS console called **cruddur**

  - In this [commit](https://github.com/imaginarydumpling/aws-bootcamp-cruddur-2023-clone/commit/4217c23968e24e59f60bbca40d4530a290dc2051#diff-5e69de896a2f2b06791ac316dc95f94b7e0e3313e2fb66f80d2c367a215fa545), we create a script that will help us view logs on a container level in ECS for our backend and frontend services.

  - In this [commit](https://github.com/imaginarydumpling/aws-bootcamp-cruddur-2023-clone/commit/4217c23968e24e59f60bbca40d4530a290dc2051#diff-370a022e48cb18faf98122794ffc5ce775b2606b09a9d1f80b71333425ec078e), we also modified the gitpod.yml file to automate the installation of session-manager. This will enable us to view the containers on our ECS.


### 3. Create containers in ECR

  - Create the python container in ECR using this terminal commands.

```

	aws ecr create-repository \
  --repository-name cruddur-python \
  --image-tag-mutability MUTABLE

```
  - After creating the python repo. Login to your ECR in gitpod terminal using this terminal command.

```
	aws ecr get-login-password --region $AWS_DEFAULT_REGION|docker login --username AWS --password-stdin "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com"

```
  - Get the URI of the cruddur-python repo created in ECR. Then run this command.

```
	docker pull python:3.10-slim-buster
	docker tag python:3.10-slim-buster $ECR_PYTHON_URL:3.10-slim-buster
docker push $ECR_PYTHON_URL:3.10-slim-buster
```

  - We will create another repository for the backend-flask using this terminal command. 

```
	aws ecr create-repository \
  --repository-name backend-flask \
  --image-tag-mutability MUTABLE

```      
  - Run these commands in the terminal to create an ENV_VAR for the backend-flask URI

```
export ECR_BACKEND_FLASK_URL="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com/backend-flask"
echo $ECR_BACKEND_FLASK_URL
```

  - We will run these set of commands to tag and push the docker image to our created ECR repo.

```
docker tag backend-flask:latest $ECR_BACKEND_FLASK_URL:latest
docker push $ECR_BACKEND_FLASK_URL:latest
``` 


### 4. Adding ENV VARS to AWS System Manager Parameter Store

  - Type these commands in gitpot terminal.
  
  ```
  aws ssm put-parameter --type "SecureString"--name "/cruddur/backend-flask/AWS_ACCESS_KEY_ID"--value $AWS_ACCESS_KEY_ID
	aws ssm put-parameter --type "SecureString"--name "/cruddur/backend-flask/AWS_SECRET_ACCESS_KEY"--value $AWS_SECRET_ACCESS_KEY
	aws ssm put-parameter --type "SecureString"--name "/cruddur/backend-flask/CONNECTION_URL"--value $PROD_CONNECTION_URL
	aws ssm put-parameter --type "SecureString"--name "/cruddur/backend-flask/ROLLBAR_ACCESS_TOKEN"--value $ROLLBAR_ACCESS_TOKEN
  aws ssm put-parameter --type "SecureString"--name "/cruddur/backend-flask/OTEL_EXPORTER_OTLP_HEADERS"--value "x-honeycomb-team=$HONEYCOMB_API_KEY"
  ```
  - These commands will import the necessary local env vars to our parameter store in secured way. These parameters will be used to reference them in our backend and frontend repositories in ECR.

  - [reference](	Reference:
https://docs.aws.amazon.com/AmazonECS/latest/developerguide/specifying-sensitive-data.html )
  -[reference]( https://docs.aws.amazon.com/AmazonECS/latest/developerguide/secrets-envvar-ssm-paramstore.html) 


### 5. Adding roles and policies for ECS tasks and services

  - With the policies created in aws/policies. Run these commands.

```
aws iam create-role \
    --role-name CruddurTaskRole \
    --assume-role-policy-document "{
  \"Version\":\"2012-10-17\",
  \"Statement\":[{
    \"Action\":[\"sts:AssumeRole\"],
    \"Effect\":\"Allow\",
    \"Principal\":{
      \"Service\":[\"ecs-tasks.amazonaws.com\"]
    }
  }]
}"

aws iam put-role-policy \
  --policy-name SSMAccessPolicy \
  --role-name CruddurTaskRole \
  --policy-document "{
  \"Version\":\"2012-10-17\",
  \"Statement\":[{
    \"Action\":[
      \"ssmmessages:CreateControlChannel\",
      \"ssmmessages:CreateDataChannel\",
      \"ssmmessages:OpenControlChannel\",
      \"ssmmessages:OpenDataChannel\"
    ],
    \"Effect\":\"Allow\",
    \"Resource\":\"*\"
  }]
}
"

aws iam attach-role-policy --policy-arn arn:aws:iam::aws:policy/CloudWatchFullAccess --role-name CruddurTaskRole
aws iam attach-role-policy --policy-arn arn:aws:iam::aws:policy/AWSXRayDaemonWriteAccess --role-name CruddurTaskRole
```

  - Running these commands will create a policy called 'CruddurTaskRole' with the right permission policies


### 6. Running service in Cruddur cluster

  - Run this command to run backend service in cruddur cluster.

```
aws ecs create-service --cli-input-json file://aws/json/service-backend-flask.json
```

  - After creating the service we can verify the healthiness of our container by using the connect-to-service script and adding the session id of the current running tasks in backend-flask service  

  - We can also check the health-checks via the {$PUBLIC_ID}:4567/api/health-check. 
  This is the one we setup earlier as an health-check endpoint in app.py





### 7. Setup a load balancer

  - Navigate to EC2 and find the Load Balancer. Click create Load Balancer 