# Week 1 — App Containerization


### 1. Worked on half of the checklist
  ![image](https://user-images.githubusercontent.com/56792014/220051713-6a5c386e-ee6f-4acd-af9a-566762c8a9a5.png)
  
### 2. Worked on adding the notifications feature both on Frontend and Backend
![image](https://user-images.githubusercontent.com/56792014/220064570-be7187dd-3314-4eb7-b3f4-3d4fe167dc8f.png)

- Created a file in backend-flask/DockerFile
          
```
FROM python:3.10-slim-buster

WORKDIR /backend-flask

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY . .

ENV FLASK_ENV=development

EXPOSE ${PORT}
CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0", "--port=4567"]
```

- Build backend-flask container
```
docker build -t  backend-flask ./backend-flask
```

- Run container
```
docker run --rm -p 4567:4567 -it -e FRONTEND_URL='*' -e BACKEND_URL='*' backend-flask 
```

- Created a file in frontend-react-js/DockerFile
```
FROM node:16.18

ENV PORT=3000

COPY . /frontend-react-js
WORKDIR /frontend-react-js
RUN npm install
EXPOSE ${PORT}
CMD ["npm", "start"]
```

- Build container
```
docker build -t frontend-react-js ./frontend-react-js
```

- Run container
```
docker run -p 3000:3000 -d frontend-react-js
```        

### 3. Created docker compose file in /workspace/aws-bootcamp-cruddur-2023
 ```
version: "3.8"
services:
  backend-flask:
    environment:
      FRONTEND_URL: "https://3000-${GITPOD_WORKSPACE_ID}.${GITPOD_WORKSPACE_CLUSTER_HOST}"
      BACKEND_URL: "https://4567-${GITPOD_WORKSPACE_ID}.${GITPOD_WORKSPACE_CLUSTER_HOST}"
    build: ./backend-flask
    ports:
      - "4567:4567"
    volumes:
      - ./backend-flask:/backend-flask
  frontend-react-js:
    environment:
      REACT_APP_BACKEND_URL: "https://4567-${GITPOD_WORKSPACE_ID}.${GITPOD_WORKSPACE_CLUSTER_HOST}"
    build: ./frontend-react-js
    ports:
      - "3000:3000"
    volumes:
      - ./frontend-react-js:/frontend-react-js

# the name flag is a hack to change the default prepend folder
# name when outputting the image names
networks: 
  internal-network:
    driver: bridge
    name: cruddur
```


### 4. Worked on adding databases in gitpod.yml and docker compose
  - Modified gitpod.yml file that installs postgre whenever codespace is initiated
          
``` 
          - name: postgres
    init: |
      curl -fsSL https://www.postgresql.org/media/keys/ACCC4CF8.asc|sudo gpg --dearmor -o /etc/apt/trusted.gpg.d/postgresql.gpg
      echo "deb http://apt.postgresql.org/pub/repos/apt/ `lsb_release -cs`-pgdg main" |sudo tee  /etc/apt/sources.list.d/pgdg.list
      sudo apt update
      sudo apt install -y postgresql-client-13 libpq-dev
```

- Added postgres docker in docker-compose.yml file
```
services:
  db:
    image: postgres:13-alpine
    restart: always
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    ports:
      - '5432:5432'
    volumes: 
      - db:/var/lib/postgresql/data
volumes:
  db:
    driver: local
```

- Dynamodb local is also added in docker-compose.yml file
```
services:
  dynamodb-local:
    # https://stackoverflow.com/questions/67533058/persist-local-dynamodb-data-in-volumes-lack-permission-unable-to-open-databa
    # We needed to add user:root to get this working.
    user: root
    command: "-jar DynamoDBLocal.jar -sharedDb -dbPath ./data"
    image: "amazon/dynamodb-local:latest"
    container_name: dynamodb-local
    ports:
      - "8000:8000"
    volumes:
      - "./docker/dynamodb:/home/dynamodblocal/data"
    working_dir: /home/dynamodblocal
```

- Volume mapping
```
volumes: 
  - db:/var/lib/postgresql/data

volumes:
  db:
    driver: local
```

# HomeWork Challenges:

### 1. Push and tag an image in DockerFile
![image](https://user-images.githubusercontent.com/56792014/220115567-0b89d50b-fe34-4d98-a2dc-69834851b863.png)
 - Pushed all the image in docker-compose.yml file.


1. Re-tagged all existing local image docker tag <existing-image> <hub-user>/<repo-name>[:<tag>]
i.e
```
docker tag 904626f640dc godstwilight/cloudbootcamp:dynamodb-latest

```

2. Pushed the newly tagged docker image to docker hub repo

```
docker push godstwilight/cloudbootcamp:dynamodb-latest
```
  
3. Deleted the newly tagged docker image after pushing 

```
docker rmi godstwilight/cloudbootcamp:dynamodb-latest 
```


  
### 2. Run the dockerfile CMD as an external script

Dockerfile with CMD
```  
FROM python:3.10-slim-buster
WORKDIR /backend-flask

COPY requirements.txt requirements.txt

RUN pip3 install -r requirements.txt

COPY . .

ENV FLASK_ENV=development

EXPOSE ${PORT}

CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0", "--port=4567"]
```
  The CMD on this dockerfile should be ran by an external script. In order to do that, I used RUN and ENTRYPOINT.
  RUN will add permissions on the script file before running the script file via ENTRYPOINT which allows me to run the script file as an executable

DOCKERFILE with RUN and ENTRYPOINT to run the CMD as an external script
```
FROM python:3.10-slim-buster
WORKDIR /backend-flask

COPY requirements.txt requirements.txt

RUN pip3 install -r requirements.txt

COPY . .

ENV FLASK_ENV=development

EXPOSE ${PORT}

RUN chmod a+x script_backend.sh

ENTRYPOINT ["sh", "./script_backend.sh"] 
```

script_backend.sh
  - #!/bin/sh will tell us what command interpreter will be used which in this case would be the .sh format ![ref](https://tldp.org/LDP/abs/html/sha-bang.html#MAGNUMREF)
  - set -x would be used to see what commands would be printed out before executing the commands itself ![ref](https://www.gnu.org/software/bash/manual/html_node/The-Set-Builtin.html)
  - python3 -m flask run --host=0.0.0.0 --port=4567 is the CMD exec itself in the previous dockerfile put into a script file to run
```
#!/bin/sh

set -x

python3 -m flask run --host=0.0.0.0 --port=4567
```
  After creating the script file, we will rebuild the dockerfile with  `docker build -t  backend-flask ./backend-flask`
  Then run it with `docker container run --rm -p 4567:4567 -d backend-flask`
  The ENTRYPOINT and RUN procedure will also be executed with the dockerfile on  ./frontend-react-js before running its docker build/run command. 
  I've also done the liberty of pushing the updated images to my dockerhub repo for future usage `docker push godstwilight/aws-bootcamp-cruddur-2023-backend-flask:tagname` `docker push godstwilight/aws-bootcamp-cruddur-2023-frontend-react-js:tagname`
  
  I also done a `docker system prune` just to clean my containers and images
  
  Then run the `docker compose up` to check if everything is working as is, to which it is.
  
  ![image](https://user-images.githubusercontent.com/56792014/220344550-0556377b-4fe7-4abf-bc2d-c190eadd6d31.png)
  
  ![image](https://user-images.githubusercontent.com/56792014/220344697-fd418b4c-acb6-43d7-866d-1a0cdba01e13.png)
  
 ### 3. Launched an EC2 instance that has docker installed, and pull a container to demonstrate you can run your own docker processes.
  
  - Navigated to my non-root AWS admin account
  - Created an EC2 instance
  ![image](https://user-images.githubusercontent.com/56792014/220350881-724f93ac-a697-432c-bfd9-b08b648c1414.png)
  - Connect inside the EC2 instance via SSH or connect via AWS Instance Connect, I've used the latter
  - Wrote these set of commands in the terminal 

```
sudo apt-get update  
apt-get -y install curl
sudo apt-get docker.io
sudo su
docker pull godstwilight/aws-bootcamp-cruddur-2023-frontend-react-js:latest
docker images
docker run -p 3000:3000 -d <image id>
docker ps -a 
```
  - `sudo apt-get update` to have  package cache in the image
  - `sudo apt-get -y install curl` for connection troubleshooting just in case we run into connection issues
  - `sudo apt-get docker.io` to install docker
  - `sudo su` run as root, writing sudo every line is tedious for me :)
  - `docker pull godstwilight/aws-bootcamp-cruddur-2023-frontend-react-js:latest` to pull the image from the public docker repo
  - `docker images` check if image is in the EC2 instance
  - `docker run -p 3000:3000 -d <image id>` run the image in a container
  - `docker ps -a` check if container is running successfully

 Docker container is running successfully 
![image](https://user-images.githubusercontent.com/56792014/220352679-54a8424d-51f4-483a-ba05-beb6b7487bba.png)

  
### 4. Installed docker on local laptop and run the containers inside the gitpod workspace
    
   - Install docker locally windows with [link](https://docs.docker.com/desktop/install/windows-install/)
   - Executed these commands to pull the images from my public dockerhub
    
    ```
    #frontend image
    docker pull godstwilight/aws-bootcamp-cruddur-2023-frontend-react-js:latest

    #backend image
    docker pull godstwilight/aws-bootcamp-cruddur-2023-backend-flask:latest

    #postgre image
    docker pull godstwilight/cloudbootcamp:postgresql-latest

    #dynamodb image
    docker pull godstwilight/cloudbootcamp:dynamodb-latest

    ```
   - Create a container out of each image
    
    ```
    #FRONTEND
    docker run -p 3000:3000 -d <image id> 
   
    #BACKEND 
    docker run --rm -p 4567:4567 -d <image id> 
   
    #DATABASE
    docker run --rm -p 8000:8000 -d <dynamodb image id> 
    docker run --rm -p 5432:5432 -d <postgre image id> 
    docker ps -a
    docker images
    ```
    ![image](https://user-images.githubusercontent.com/56792014/220367292-3c89a5b0-0429-40ea-b733-3aaf8f449972.png)
    
    DOCKER DESKTOP
    ![image](https://user-images.githubusercontent.com/56792014/220367469-bdb8ceac-46a8-4b4c-a649-30f8b27cca94.png)
   
    Docker container running in localhost
    ![image](https://user-images.githubusercontent.com/56792014/220367695-933e9f8d-d0d7-4495-8702-263da51f3ef0.png)

### 5. Added an healthcheck in V3 docker compose file for the backend container

  - Inserted the code snippet below that periodically pings the server where curl errors will be treated as unhealthy [link](https://docs.docker.com/compose/compose-file/compose-file-v3/)
    
```
  healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:<container host>"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```
  
  - This will be inserted in the docker-compose.yml file
  
![image](https://user-images.githubusercontent.com/56792014/220393227-00b231aa-8c01-43d1-8d0c-42f0f17352e3.png)
  
  - We also installed curl via run command in backend dockerfile, this will enable the curl command in the health status later

```
#install curl
RUN apt-get update && apt-get install -y \
curl
```
![image](https://user-images.githubusercontent.com/56792014/220393900-796e4877-42b3-459d-b05b-afe849393871.png)

  - After setting this all up, rebuild the backend dockerfile with `docker build --pull --rm -f "backend-flask/dockerfile" -t backend-flask:latest "backend-flask" `
    
  - Then run `docker compose build ` to rebuild the docker compose file
    
  - After the rebuilds, I did `docker compose up` command (In this case I just upped the backend service to test the healthchecks)
  
![image](https://user-images.githubusercontent.com/56792014/220394732-205043d9-b80d-4dd3-a71b-76f4b7350443.png)
    
  - You can check the healthcheck logs by using this command `docker inspect --format "{{json .State.Health }}" <container name> | jq `
    
![image](https://user-images.githubusercontent.com/56792014/220395157-c4981176-9a54-453e-9c4b-f99f870bfcf1.png)
    
  - 404 error is expected in the backend, but this also shows that the healthchecks are working.
    
![image](https://user-images.githubusercontent.com/56792014/220395517-37e1a650-19fb-43ca-a3d0-418eb6d0a6a7.png)

    
    
### 6. Added an multi-stage build in the dockerfile for the frontend container

```
  # Stage 1: Build the Application
FROM node:16.18-alpine as build

WORKDIR /frontend-react-js

# Copy everything in current directory -> Put it inside the container's /frontend-react-js
COPY . /frontend-react-js

# Run npm install inside the container
RUN npm install

# Copy everthing from the current working directory -> paste inside the container's current working directory
COPY . .

# Run npm run build inside the container to compile the source code for the next stage of the process
RUN npm run build



# Stage 2: Running the Application
FROM node:16.18-alpine

ENV PORT=3000

WORKDIR /frontend-react-js

EXPOSE ${PORT}

# copy the contents of /frontend-react-js/build from build and put it in the second stage of the process.
COPY --from=build /frontend-react-js/build /frontend-react-js/build

#CMD ["npm", "start"]

# copy the startup script to the container
COPY script_frontend.sh .

# inside the container this will run the command indicated
RUN chmod a+x script_frontend.sh

# this will set our external script as an executable evertime the container is run
ENTRYPOINT ["sh", "./script_frontend.sh"]
  
```
  
- Screenshot below shows the difference with using multi-stage build vs non multi-stage build on the image size
  
  ![image](https://user-images.githubusercontent.com/56792014/221200029-f712018d-f044-46fe-be54-0d6056fff047.png)
  ![image](https://user-images.githubusercontent.com/56792014/221200051-90a43495-facd-4254-b223-e8d5e4eeb11b.png)
  
- From the original 1.15gb size of the image, we managed to downsize the image to 365.49mb while using the node-alpine image. And doing a multi-stage build further downsizes it to 119.6 mb which is roughly 100% percent less from the original size of the image

  

  
### 7. Applying Docker best practices
  - Try to find the lightest image size for my dockerfiles that can still effectively run the image. I.E using node:16.18-alpine instead of node:16.18
  - Implementing healthchecks for monitoring container status
  - Added healthcheck for the frontend container
  

  
  
  
### 8. Cloud Journey - Pick the right cloud role.
   - My current outlook on my preferred cloud role.
  
  1. The role in cloud I'm aiming for currently is Cloud Engineer/DevOps Engineer

* What skills do you have that could transfer to this role?
	- I do have experience with Python Coding, our company encourages 
	its employees to take AWS certs that has learning plans and I did take 2 AWS certs with it.
	- I do have exposure to the general AWS services (EC2, CloudWatch, S3, DynamoDB, VPCs)
	- I'm doing side projects that involves Docker and CI/CD pipelines with some AWS service integrations
	 

* Are you interested more in people, or in data?
	- Both I'd say, my previous work needed me to be with other people
	to collaborate on finishing tasks. This is where my soft skills are 
	cultivated 

* Do you like to work alone, or more in a team?
	- I'd like working alone if the workload is sustainable,
	- Working in a team is also not so bad since I can learn some stuff from them

* What are the jobs available in your local area?
	- Lots of DevOps and Cloud Engineer roles that are masked as Front-end/Full Stack
	- I have to depend on the job descriptions to help me filter what fits my current stack


2. I will be successful in this role because… I've loved the idea of doing something critically important and solving it.

* What do you know about what this role does?* What does it take to be successful at this role?
	- They're the one responsible for the infrastructure of the application
	- They will be the one to have an overall understanding of the whole product and
	what improvements should be made with it going forward

* What about your current skills makes you a good fit for the role?
	- Not yet, I may have the soft skills as of now. But my technical expertise is nowhere 
	near on a level where I can provide value to the client/project 


* Is this role a good fit given my level of experience?
	- Not yet, I have exposure to other tech (SAP). But the DevOps stack is a different tech
	that requires dedication on learning how to implement it

* Are there sufficient jobs with this role profile in my area?
	- Yes there are.

3. - The FIVE skills I will learn are… Docker, AWS Services, CI/CD Pipelines (Github Actions), Terraform, Python

4. - The skills I will NOT learn are… Other cloud providers (Azure/GCP), Machine learning/AI, Web Dev, Crypto
