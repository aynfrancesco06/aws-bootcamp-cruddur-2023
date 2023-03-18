# Week 4 — Postgres and RDS


### 1. Create RDS Postgres Instance
  
  I've used the prescribed code snippet for provisioning an RDS instance via AWS CLI, this is doable also via the AWS RDS GUI. This code snippet is from the AWS documentation here [link](https://docs.aws.amazon.com/cli/latest/reference/rds/)

```
aws rds create-db-instance \
  --db-instance-identifier cruddur-db-instance \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --engine-version  14.6 \
  --master-username cruddurroot \
  --master-user-password <yourpassword> \
  --allocated-storage 20 \
  --availability-zone us-east-1a \
  --backup-retention-period 0 \
  --port 5432 \
  --no-multi-az \
  --db-name cruddur \
  --storage-type gp2 \
  --publicly-accessible \
  --storage-encrypted \
  --enable-performance-insights \
  --performance-insights-retention-period 7 \
  --no-deletion-protection 

```
![image](https://user-images.githubusercontent.com/56792014/226118569-a450c2b6-cd99-4a91-b9d9-0afd142fe594.png)


- This code will be pasted in the terminal on your Gitpod Codespace. Other part of the code snippet like '**master-username**' and '**master-user-password**' will be different.

- engine-version refers to the version of the database will be used. In this case, we will use postgres 14.6 version.
- availability zone should be set to where you usually provision resources. In my case its use-east-1a
- no multi az to save costs
- storage encrypted for security

After inputting this code. The result will be shown in your AWS RDS. 

![image](https://user-images.githubusercontent.com/56792014/226118774-25c6b74c-0628-4e50-8a43-3cbee71436c8.png)


If the RDS instance is not being used. We can temporarily stop the instance to avoid going beyond the Free Tier and incurring costs.
  
![image](https://user-images.githubusercontent.com/56792014/226118934-525a40ca-b48f-4703-a939-b9dbc4299e09.png)



### 2. Create bash scripts for easier DB deployment (either prod or local)




### 3. Installed Postgres driver in Backend App

### 4. Connected Gitpod IP to RDS Instance

### 5. Create a Cognito Trigger that inserts user into database

### 6. Create new activities with a database insert 
