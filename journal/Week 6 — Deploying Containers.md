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
![image](https://user-images.githubusercontent.com/127114703/231162445-124ecf44-9643-40db-aa6e-f7af47d0a68f.png)


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

![image](https://user-images.githubusercontent.com/127114703/231162508-06e8cd38-4f34-45b3-960b-9172aedf4d56.png)


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
  - We will also create a cloudwatch group for our fargate-cluster using these terminal commands

```
aws logs create-log-group --log-group-name cruddur/fargate-cluster
aws logs put-retention-policy --log-group-name cruddur/fargate-cluster --retention-in-days 1
```
  - Results should be like this 
 ![image](https://user-images.githubusercontent.com/127114703/231162083-42592da8-6ea0-4962-ae4c-b5651f0bf28b.png)



### 6. Running service in Cruddur cluster

  - Run this command to run backend service in cruddur cluster.

```
aws ecs create-service --cli-input-json file://aws/json/service-backend-flask.json
```

  - After creating the service we can verify the healthiness of our container by using the connect-to-service script and adding the session id of the current running tasks in backend-flask service  

  - We can also check the health-checks via the {$PUBLIC_ID}:4567/api/health-check. 
  This is the one we setup earlier as an health-check endpoint in app.py


### 7. Creating Load Balancer

  - We will create a Load Balancer via AWS GUI
  - Click on 'Create Load Balancer'
  - Application Load Balancer with a name of cruddur-alb
  - Internet facing and dual stack
  - Use default VPC and choose the AZ's under the VPC, we can also use command terminals to determine what is the default VPC and find the respective AZ's under that VPC 

```
export DEFAULT_VPC_ID=$(aws ec2 describe-vpcs \
--filters "Name=isDefault, Values=true" \
--query "Vpcs[0].VpcId" \
--output text)
echo $DEFAULT_VPC_ID

export DEFAULT_SUBNET_IDS=$(aws ec2 describe-subnets  \
 --filters Name=vpc-id,Values=$DEFAULT_VPC_ID \
 --query 'Subnets[*].SubnetId' \
 --output json | jq -r 'join(",")')
echo $DEFAULT_SUBNET_IDS
```
  - We will also create target groups here for frontend and backend 
![image](https://user-images.githubusercontent.com/127114703/231167338-f28f4260-bd6d-4f24-82a1-6484b930bd6c.png)
![image](https://user-images.githubusercontent.com/127114703/231167403-08828afa-ca40-451c-89c3-1d440729ac26.png)
 
 
  - Add listener tags and point 443 to our frontend target and 80 to the backend.
 
  - Finish the creation after, result should show like this
![image](https://user-images.githubusercontent.com/127114703/231167750-5bff0c07-b6c7-409e-af6f-2dc391f88a5a.png)

  


### 8. Create frontend build 
  - In this [commit](https://github.com/imaginarydumpling/aws-bootcamp-cruddur-2023-clone/commit/d404e940fc7fa15730c660582a102306bf41d438#diff-e6843ade525f0a7ca02583ea7f8310878228cb53977ad3c62dfa7e16a7f8b67e), we added a load balancer for our frontend-react-js and we will use the load balancer dns to view if the frontend is working publicly. We also added an nginx in our dockerfile for reverse proxy. We've also created a new Dockerfile.prod for our frontend-react-js container here [commit](https://github.com/imaginarydumpling/aws-bootcamp-cruddur-2023-clone/commit/4217c23968e24e59f60bbca40d4530a290dc2051#diff-7c2adaca3e31bca71bdaf16d8980ce69b0f8125cbfddaf9d36f58ca7ef3e799b)
  
  - Run these set of commands to build and push the frontend-react-js build to ECR.
 
```
docker build \
--build-arg REACT_APP_BACKEND_URL="https://4567-$GITPOD_WORKSPACE_ID.$GITPOD_WORKSPACE_CLUSTER_HOST" \
--build-arg REACT_APP_AWS_PROJECT_REGION="$AWS_DEFAULT_REGION" \
--build-arg REACT_APP_AWS_COGNITO_REGION="$AWS_DEFAULT_REGION" \
--build-arg REACT_APP_AWS_USER_POOLS_ID="<YOUR USER ID POOL>" \
--build-arg REACT_APP_CLIENT_ID="< YOUR APP CLIENT ID>" \
-t frontend-react-js \
-f Dockerfile.prod \
.
```

```
docker tag frontend-react-js:latest $ECR_FRONTEND_REACT_URL:latest
docker push $ECR_FRONTEND_REACT_URL:latest
```
  - We will also add health-checks on a container level for our frontend task definition here in this [commit](https://github.com/imaginarydumpling/aws-bootcamp-cruddur-2023-clone/commit/b12a543219f146ea1ec643007c0a74d683ba9917#diff-b1ee9974828856aa33e1eae739e5a1e7b07a9bdbee3b5665e040a451cba663ff)

  - After pushing the file, we can register the task definitions for frontend-react-js and launch create service.
  - Result should be showing the Homepage with the address directed to our created load balancer
 
 
### 9. Created Hosted Zone
 
   - In this [commit](https://github.com/imaginarydumpling/aws-bootcamp-cruddur-2023-clone/commit/a503931adae92ef296c0c7d92ac04e6cd017443b#diff-fce4cbfaaa6ae500dea2961ebd2e8395ff961a7a764b1cebc1f11325d50a2866), the env vars are modified to point to the created hosted zone in our AWS account. This will enable to route the backend and frontend to our domain hosted in AWS Route 53 Hosted Zone
   - We will also create a hosted zone in AWS Route 53
   - Click on create hosted zone, put the domain name of the domain you bought. in my case its thecloudproject.store and set to public hosted zone
   - After creation copy the NS generated by your hosted zone and put it in the custom DNS of your domain registrar, which in my case is namecheap. Wait for a few hours to propagate the new DNS after setting up your NS.
  ![image](https://user-images.githubusercontent.com/127114703/231169461-75fb99f1-0ede-4b24-8406-c0726654115e.png)

  - Navigate to ACM to create certificates for our hosted zone domain.
  - Click on request a public certificate
  - Enter domain name, thecloudproject.store and *.thecloudproject.store
  - DNS validation
  - Everything else leave on default
  - Click on request
  - Click on the created certificate and Create Records in route 53, create the records for both domain created earlier in the ACM.
  - The created records from ACM should reflect in the Route 53 Hosted Zone as a CNAME
![image](https://user-images.githubusercontent.com/127114703/231170253-88eb4838-b50c-4a95-bedc-142b7c894897.png)

  - Create 2 Alias for thecloudproject.store and api.thecloudproject.store point it both to our ALB
  - After point it to our ALB, we should be able to access our application over our domain name.

![image](https://user-images.githubusercontent.com/127114703/231170856-137e7b88-5c8d-4422-b80c-f6e21525f9af.png)


### 10. Create docker build scripts for frontend and backend container

  - In this [commit](https://github.com/imaginarydumpling/aws-bootcamp-cruddur-2023-clone/commit/2d2b1c37ef474cfa68a4c7566882f8966487e2ea#diff-ce68e9fcfe8d8a8400d12b8e17539923971918424922298d21f7ef6f30edd299), I've added a docker build scripts for our front-end and back-end. We've also moved the bin folder to top level to make it easier to run the scripts. 
The pathing of the scripts is also fixed in this [commit](https://github.com/imaginarydumpling/aws-bootcamp-cruddur-2023-clone/commit/93e84351a7515173d1e358718872d2d6286813e3#diff-e6a925f624a2dcc9ae564564b16aa035e6938165abe353a7a5759fa9f37ca681)

 - We added a force deploy here in this [commit](https://github.com/imaginarydumpling/aws-bootcamp-cruddur-2023-clone/commit/e41d8df7535f70020b64624091a0ff2e98ba27de) which should be ran after running the build and push scripts for our frontend and backend

### 11. Implementing messages in our production

 - Message implementation is tackled here in this [commit](https://github.com/imaginarydumpling/aws-bootcamp-cruddur-2023-clone/commit/631f6e8f0b9d16bad0bde6812877094153b64b6f) as well as troubleshooting some code here [commit](https://github.com/imaginarydumpling/aws-bootcamp-cruddur-2023-clone/commit/63dfaf039bc8e063ac7e32bbc8ebfd4c06b4367c#diff-0014cc1f7ffd53e63ff797f0f2925a994fbd6797480d9ca5bbc5dc65f1b56438) 


### 12. Modifying our env vars

 - This [commit](https://github.com/imaginarydumpling/aws-bootcamp-cruddur-2023-clone/commit/5bb0c14ee204cfbcb860c50550cb8d2502823e0b) focuses on removing the env vars in our docker compose file and putting it on a separate script that generates a env.file.


### 13. Adding ECS Insights

  - This [commit](https://github.com/imaginarydumpling/aws-bootcamp-cruddur-2023-clone/commit/82d49f9cd60cc747506ffeff4a534798b2c639af) shows where we added an aws-xray-daemon for ECS Insights, this would allow us to have more visibility in the problems happening within our ECS Containers. We've also created a register script to automate the container register before being deployed in the deploy register script.

### 14. Refresh Token Cognito

  - This [commit](https://github.com/imaginarydumpling/aws-bootcamp-cruddur-2023-clone/commit/9db78125cedac60ec6c76d73943b47c269004d0a#diff-fce4cbfaaa6ae500dea2961ebd2e8395ff961a7a764b1cebc1f11325d50a2866) focuses on implementing refresh token cognito.
  - Our checkAuth [here](https://github.com/imaginarydumpling/aws-bootcamp-cruddur-2023-clone/commit/9db78125cedac60ec6c76d73943b47c269004d0a#diff-716a46d7255bdc7f3c7c1f5f463d4580b0f4dcb288e9027b432ea13e8baebdf9) is modified and the access_token will be used across other pages as the bearer token [HomeFeedPage](https://github.com/imaginarydumpling/aws-bootcamp-cruddur-2023-clone/commit/9db78125cedac60ec6c76d73943b47c269004d0a#diff-292834603c08709370ba2559a46a774323654828319cad0f1725ab83a5f41537) [MessageGroupNewpage](https://github.com/imaginarydumpling/aws-bootcamp-cruddur-2023-clone/commit/9db78125cedac60ec6c76d73943b47c269004d0a#diff-19e1c41053ae4fc921364047da3f3c2e049950392fd522cbd1605a57ded7312b) [MessageGroupPage](https://github.com/imaginarydumpling/aws-bootcamp-cruddur-2023-clone/commit/9db78125cedac60ec6c76d73943b47c269004d0a#diff-7932be144100c97223bc212a13afa0b412f89e80ec7d3691a5901066a2765325) [MessageGroupsPage](https://github.com/imaginarydumpling/aws-bootcamp-cruddur-2023-clone/commit/9db78125cedac60ec6c76d73943b47c269004d0a#diff-6fe73cc7bc0f0c7934716b6c0b2a70902b39626ffc13d6ca161aed6cfc3fe54d) [MessageForm](https://github.com/imaginarydumpling/aws-bootcamp-cruddur-2023-clone/commit/9db78125cedac60ec6c76d73943b47c269004d0a#diff-7cf22502ee0acb0e53dcb9131f62f9074c7232526249db46d5d2d32c11af1633)


Verifying messaging in prod working

![image](https://user-images.githubusercontent.com/127114703/231194167-df32e4ac-a744-48c3-b770-716c83a0c427.png)


Refresh token working

![image](https://user-images.githubusercontent.com/127114703/231194260-9f55410a-6bce-4009-833a-a040109f44ac.png)

### 15. Fixing timezones issues fir ISO 8601

  - This [commit](https://github.com/imaginarydumpling/aws-bootcamp-cruddur-2023-clone/commit/e2eda259adeb214b0f27a6f9a9dc0116e3f39e27) shows a new file being added called DateTimeFormat.js where we will use the UTC timezone as our reference for how many minutes have passed after posting a message or activity in the homepage.
  - The functions inside it will be referenced to many files in frontend-react-js/src/components
  - Results should be like this after the said changes.

![image](https://user-images.githubusercontent.com/127114703/231249295-146ba3d6-e85a-4b87-a94e-2b43e2b5f7c9.png)


![image](https://user-images.githubusercontent.com/127114703/231249329-633d79ad-0eac-4b05-9281-16a832081905.png)

