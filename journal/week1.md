# Week 1 — App Containerization


#### 1. Worked on half of the checklist
  ![image](https://user-images.githubusercontent.com/56792014/220051713-6a5c386e-ee6f-4acd-af9a-566762c8a9a5.png)
  
#### 2. Worked on adding the notifications feature both on Frontend and Backend
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

#### 3. Created docker compose file in /workspace/aws-bootcamp-cruddur-2023
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


#### 4. Worked on adding databases in gitpod.yml and docker compose
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

#### 1. Push and tag an image in DockerFile
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


  
#### 2. Run the dockerfile CMD as an external script

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
  
 #### 3. Launched an EC2 instance that has docker installed, and pull a container to demonstrate you can run your own docker processes.
  
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

