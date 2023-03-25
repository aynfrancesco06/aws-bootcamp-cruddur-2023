# Week 5 — DynamoDB and Serverless Caching



### 1. Implement Schema Load Script

##### Context:
  - We will use a schema-load python script that will create a table in dynamodb.


##### Steps:
  - Add boto3 in our backend-flask through requirements.txt file
![image](https://user-images.githubusercontent.com/56792014/227713852-9e107248-128d-46d8-93dd-ad8b31f4109a.png)

  - We will add a new folder called **ddb** inside our bin folder. This will contain all the scripts necessary for connecting our app with dynamodb
  - We will then creating a file called **schema-load** inside our ddb folder, this will create a data table called **cruddur-messages** in our dynamodb

schema-load.py
```
#!/usr/bin/env python3

import boto3
import sys

attrs = {
    'endpoint_url':'http://localhost:8000'
}

if len(sys.argv) == 2:
    if "prod" in sys.argv[1]:
        attrs = {}

ddb = boto3.client('dynamodb', **attrs)

table_name = 'cruddur-messages'





response = ddb.create_table(
    TableName=table_name,
    AttributeDefinitions=[
        {
            'AttributeName': 'pk',
            'AttributeType': 'S'
        },
        {
            'AttributeName': 'message_group_uuid',
            'AttributeType': 'S'
        },
        {
            'AttributeName': 'sk',
            'AttributeType': 'S'
        }
    ],
    KeySchema=[
        {
            'AttributeName': 'pk',
            'KeyType': 'HASH'
        },
        {
            'AttributeName': 'sk',
            'KeyType': 'RANGE'
        },
    ],
    BillingMode='PROVISIONED',
    ProvisionedThroughput={
        'ReadCapacityUnits': 5,
        'WriteCapacityUnits': 5
    },
    GlobalSecondaryIndexes=   [{
    'IndexName':'message-group-sk-index',
    'KeySchema':[{
        'AttributeName': 'message_group_uuid',
        'KeyType': 'HASH'
    },{
        'AttributeName': 'sk',
        'KeyType': 'RANGE'
    }],
        'Projection': {
        'ProjectionType': 'ALL'
    },
        'ProvisionedThroughput': {
        'ReadCapacityUnits': 5,
        'WriteCapacityUnits': 5
    },
    }]
)


print(response)
```
  - 



### 2. Implement Seed Script

##### Context:
  - We will use a schema-load python script that will create a table inside our existing AWS RDS.


##### Steps:


### 3. Implement Scan Script	

##### Context:
  - We will use a schema-load python script that will create a table inside our existing AWS RDS.


##### Steps:

### 4. Implement Pattern Scripts for Read and List Conversations	

##### Context:
  - We will use a schema-load python script that will create a table inside our existing AWS RDS.


##### Steps:

### 5. Implement Update Cognito ID Script for Postgres Database	

##### Context:
  - We will use a schema-load python script that will create a table inside our existing AWS RDS.


##### Steps:

### 6. Implement (Pattern A) Listing Messages in Message Group into Application	

##### Context:
  - We will use a schema-load python script that will create a table inside our existing AWS RDS.


##### Steps:

### 7. Implement (Pattern B) Listing Messages Group into Application	

##### Context:
  - We will use a schema-load python script that will create a table inside our existing AWS RDS.


##### Steps:

### 8. Implement (Pattern B) Listing Messages Group into Application	

##### Context:
  - We will use a schema-load python script that will create a table inside our existing AWS RDS.


##### Steps:

### 9. Implement (Pattern C) Creating a Message for an existing Message Group into Application	

##### Context:
  - We will use a schema-load python script that will create a table inside our existing AWS RDS.


##### Steps:

### 10. Implement (Pattern D) Creating a Message for a new Message Group into Application	

##### Context:
  - We will use a schema-load python script that will create a table inside our existing AWS RDS.


##### Steps:

### 11. Implement (Pattern E) Updating a Message Group using DynamoDB Streams	

##### Context:
  - We will use a schema-load python script that will create a table inside our existing AWS RDS.


##### Steps:
