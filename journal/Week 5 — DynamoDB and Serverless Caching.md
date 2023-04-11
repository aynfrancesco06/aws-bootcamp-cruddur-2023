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
            'AttributeName': 'message_group_uuid', # this is added for dynamodb streams integration
            'AttributeType': 'S' # this is added for dynamodb streams integration
        },
        {
            'AttributeName': 'sk',
            'AttributeType': 'S'
        }
    ],
    KeySchema=[
        {
            'AttributeName': 'pk', # means primary key
            'KeyType': 'HASH'
        },
        {
            'AttributeName': 'sk', # secondary key
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
  - use the **chmod u+x ./bin/ddb/schema-load** to allow execution on the script and then run the script.
  
  - Running the script will show result like below
![image](https://user-images.githubusercontent.com/56792014/227721466-e51e0a00-f82f-49d4-a61c-1d859294fa4c.png)

  - We will also create a **list-table** script to verify if the schema is loaded in our dynamodb. Use the **chmod u+x** to validate the script as an executable.
  
list-tables
```
#! /usr/bin/bash

set -e

if [ "$1" = "prod" ]; then
    ENDPOINT_URL=""
else
    ENDPOINT_URL="--endpoint-url=http://localhost:8000"
fi

aws dynamodb list-tables $ENDPOINT_URL \
--query TableNames \
--output table

```

  - Result should look like this if schema-load script run successfully
![image](https://user-images.githubusercontent.com/56792014/227721600-f9fa3c0c-5d5d-487a-84db-59bbd6d570e2.png)



  - We will also create drop script, to drop the table whenever we want. This will be placed in the same ddb folder.

drop.py
```
#! /usr/bin/bash

set -e

if [ -z "$1" ]; then
    echo "No TABLE_NAME argument supplied eg.. ./bin/ddb/drop cruddur-messages prod"
    exit 1
fi
TABLE_NAME=$1 

if [ "$2" = "prod" ]; then
    ENDPOINT_URL=""
else
    ENDPOINT_URL="--endpoint-url=http://localhost:8000"
fi

echo "delete table name: $TABLE_NAME"

aws dynamodb delete-table $ENDPOINT_URL \
    --table-name $TABLE_NAME
```

  - Result should be like this if you type **drop cruddur-messages**
  ![image](https://user-images.githubusercontent.com/56792014/227721804-17181e21-3db4-4045-8cd3-0343853f35b0.png)




### 2. Implement Seed Script

##### Context:
  - - This script loads artificial data to the database that will simulate a message conversation between 2 users. We will place this inside our ddb folder. Will also add a **chmod u+x** modification to the file.


##### Steps:

seed.py
```
#!/usr/bin/env python3

import boto3
from datetime import datetime, timedelta, timezone
import os
import sys
import uuid

current_path = os.path.dirname(os.path.abspath(__file__))
parent_path = os.path.abspath(os.path.join(current_path, '..', '..'))
sys.path.append(parent_path)
from lib.db import db

attrs = {
  'endpoint_url': 'http://localhost:8000'
}

# unset endpoint url for use with production database
if len(sys.argv) == 2:
  if "prod" in sys.argv[1]:
    attrs = {}
ddb = boto3.client('dynamodb',**attrs)


# this will capture the handle that matches the conditions and return it as 'my_user' and 'other_user'
# this function will be used later to call attributes contained in the function
def get_user_uuids():
  sql = """
    SELECT 
      users.uuid,
      users.display_name,
      users.handle
    FROM users
    WHERE
      users.handle IN(
        %(my_handle)s,
        %(other_handle)s
        )
  """

  users = db.query_array_json(sql,{
    'my_handle':  'andrewbrown',
    'other_handle': 'krappa'
  })
  my_user    = next((item for item in users if item["handle"] == 'andrewbrown'), None)
  other_user = next((item for item in users if item["handle"] == 'krappa'), None)
  results = {
    'my_user': my_user,
    'other_user': other_user
  }
  print('get_user_uuids')
  print(results)
  return results

# the function is pulling the records for dynamodb, the record variable contents is from the dynamodb excel sheet where we list all the attributes
def create_message_group(client,message_group_uuid, my_user_uuid, last_message_at=None, message=None, other_user_uuid=None, other_user_display_name=None, other_user_handle=None):
  table_name = 'cruddur-messages'
  record = {
    'pk':   {'S': f"GRP#{my_user_uuid}"},
    'sk':   {'S': last_message_at},
    'message_group_uuid': {'S': message_group_uuid},
    'message':  {'S': message},
    'user_uuid': {'S': other_user_uuid},
    'user_display_name': {'S': other_user_display_name},
    'user_handle': {'S': other_user_handle}
  }

  response = client.put_item(
    TableName=table_name,
    Item=record
  )
  print(response)


# the record data is from dynamodb excel sheet
def create_message(client,message_group_uuid, created_at, message, my_user_uuid, my_user_display_name, my_user_handle):
  table_name = 'cruddur-messages'
  record = {
    'pk':   {'S': f"MSG#{message_group_uuid}"},
    'sk':   {'S': created_at },
    'message_uuid': { 'S': str(uuid.uuid4()) },
    'message': {'S': message},
    'user_uuid': {'S': my_user_uuid},
    'user_display_name': {'S': my_user_display_name},
    'user_handle': {'S': my_user_handle}
  }
  # insert the record into the table
  response = client.put_item(
    TableName=table_name,
    Item=record
  )
  # print the response
  print(response)



message_group_uuid = "5ae290ed-55d1-47a0-bc6d-fe2bc2700399" 
now = datetime.now(timezone.utc).astimezone()
users = get_user_uuids()


create_message_group(
  client=ddb,
  message_group_uuid=message_group_uuid,
  my_user_uuid=users['my_user']['uuid'],
  other_user_uuid=users['other_user']['uuid'],
  other_user_handle=users['other_user']['handle'],
  other_user_display_name=users['other_user']['display_name'],
  last_message_at=now.isoformat(),
  message="this is a filler message"
)

create_message_group(
  client=ddb,
  message_group_uuid=message_group_uuid,
  my_user_uuid=users['other_user']['uuid'],
  other_user_uuid=users['my_user']['uuid'],
  other_user_handle=users['my_user']['handle'],
  other_user_display_name=users['my_user']['display_name'],
  last_message_at=now.isoformat(),
  message="this is a filler message"
)




conversation = """
Person 1: Have you ever watched Babylon 5? It's one of my favorite TV shows!
Person 2: Yes, I have! I love it too. What's your favorite season?
Person 1: I think my favorite season has to be season 3. So many great episodes, like "Severed Dreams" and "War Without End."
Person 2: Yeah, season 3 was amazing! I also loved season 4, especially with the Shadow War heating up and the introduction of the White Star.
Person 1: Agreed, season 4 was really great as well. I was so glad they got to wrap up the storylines with the Shadows and the Vorlons in that season.
Person 2: Definitely. What about your favorite character? Mine is probably Londo Mollari.
Person 1: Londo is great! My favorite character is probably G'Kar. I loved his character development throughout the series.
Person 2: G'Kar was definitely a standout character. I also really liked Delenn's character arc and how she grew throughout the series.
Person 1: Delenn was amazing too, especially with her role in the Minbari Civil War and her relationship with Sheridan. Speaking of which, what did you think of the Sheridan character?
Person 2: I thought Sheridan was a great protagonist. He was a strong leader and had a lot of integrity. And his relationship with Delenn was so well-done.
Person 1: I totally agree! I also really liked the dynamic between Garibaldi and Bester. Those two had some great scenes together.
Person 2: Yes! Their interactions were always so intense and intriguing. And speaking of intense scenes, what did you think of the episode "Intersections in Real Time"?
Person 1: Oh man, that episode was intense. It was so well-done, but I could barely watch it. It was just too much.
Person 2: Yeah, it was definitely hard to watch. But it was also one of the best episodes of the series in my opinion.
Person 1: Absolutely. Babylon 5 had so many great episodes like that. Do you have a favorite standalone episode?
Person 2: Hmm, that's a tough one. I really loved "The Coming of Shadows" in season 2, but "A Voice in the Wilderness" in season 1 was also great. What about you?
Person 1: I think my favorite standalone episode might be "The Long Twilight Struggle" in season 2. It had some great moments with G'Kar and Londo.
Person 2: Yes, "The Long Twilight Struggle" was definitely a standout episode. Babylon 5 really had so many great episodes and moments throughout its run.
Person 1: Definitely. It's a shame it ended after only five seasons, but I'm glad we got the closure we did with the series finale.
Person 2: Yeah, the series finale was really well-done. It tied up a lot of loose ends and left us with a great sense of closure.
Person 1: It really did. Overall, Babylon 5 is just such a great show with fantastic characters, writing, and world-building.
Person 2: Agreed. It's one of my favorite sci-fi shows of all time and I'm always happy to revisit it.
Person 1: Same here. I think one of the things that makes Babylon 5 so special is its emphasis on politics and diplomacy. It's not just a show about space battles and aliens, but about the complex relationships between different species and their political maneuvering.
Person 2: Yes, that's definitely one of the show's strengths. And it's not just about big-picture politics, but also about personal relationships and the choices characters make.
Person 1: Exactly. I love how Babylon 5 explores themes of redemption, forgiveness, and sacrifice. Characters like G'Kar and Londo have such compelling arcs that are driven by their choices and actions.
Person 2: Yes, the character development in Babylon 5 is really top-notch. Even minor characters like Vir and Franklin get their moments to shine and grow over the course of the series.
Person 1: I couldn't agree more. And the way the show handles its themes is so nuanced and thought-provoking. For example, the idea of "the one" and how it's used by different characters in different ways.
Person 2: Yes, that's a really interesting theme to explore. And it's not just a one-dimensional concept, but something that's explored in different contexts and with different characters.
Person 1: And the show also does a great job of balancing humor and drama. There are so many funny moments in the show, but it never detracts from the serious themes and the high stakes.
Person 2: Absolutely. The humor is always organic and never feels forced. And the show isn't afraid to go dark when it needs to, like in "Intersections in Real Time" or the episode "Sleeping in Light."
Person 1: Yeah, those episodes are definitely tough to watch, but they're also some of the most powerful and memorable episodes of the series. And it's not just the writing that's great, but also the acting and the production values.
Person 2: Yes, the acting is fantastic across the board. From Bruce Boxleitner's performance as Sheridan to Peter Jurasik's portrayal of Londo, every actor brings their A-game. And the production design and special effects are really impressive for a TV show from the 90s.
Person 1: Definitely. Babylon 5 was really ahead of its time in terms of its visuals and special effects. And the fact that it was all done on a TV budget makes it even more impressive.
Person 2: Yeah, it's amazing what they were able to accomplish with the limited resources they had. It just goes to show how talented the people behind the show were.
Person 1: Agreed. It's no wonder that Babylon 5 has such a devoted fanbase, even all these years later. It's just such a well-crafted and timeless show.
Person 2: Absolutely. I'm glad we can still appreciate it and talk about it all these years later. It really is a show that stands the test of time.
Person 1: One thing I really appreciate about Babylon 5 is how it handles diversity and representation. It has a really diverse cast of characters from different species and backgrounds, and it doesn't shy away from exploring issues of prejudice and discrimination.
Person 2: Yes, that's a great point. The show was really ahead of its time in terms of its diverse cast and the way it tackled issues of race, gender, and sexuality. And it did so in a way that felt natural and integrated into the story.
Person 1: Definitely. It's great to see a show that's not afraid to tackle these issues head-on and address them in a thoughtful and nuanced way. And it's not just about representation, but also about exploring different cultures and ways of life.
Person 2: Yes, the show does a great job of world-building and creating distinct cultures for each of the species. And it's not just about their physical appearance, but also about their customs, beliefs, and values.
Person 1: Absolutely. It's one of the things that sets Babylon 5 apart from other sci-fi shows. The attention to detail and the thought that went into creating this universe is really impressive.
Person 2: And it's not just the aliens that are well-developed, but also the human characters. The show explores the different factions and political ideologies within EarthGov, as well as the different cultures and traditions on Earth.
Person 1: Yes, that's another great aspect of the show. It's not just about the conflicts between different species, but also about the internal struggles within humanity. And it's all tied together by the overarching plot of the Shadow War and the fate of the galaxy.
Person 2: Definitely. The show does a great job of balancing the episodic stories with the larger arc, so that every episode feels important and contributes to the overall narrative.
Person 1: And the show is also great at building up tension and suspense. The slow burn of the Shadow War and the mystery of the Vorlons and the Shadows kept me on the edge of my seat throughout the series.
Person 2: Yes, the show is really good at building up anticipation and delivering satisfying payoffs. Whether it's the resolution of a character arc or the climax of a season-long plotline, Babylon 5 always delivers.
Person 1: Agreed. It's just such a well-crafted and satisfying show, with so many memorable moments and characters. I'm really glad we got to talk about it today.
Person 2: Me too. It's always great to geek out about Babylon 5 with someone who appreciates it as much as I do!
Person 1: Yeah, it's always fun to discuss our favorite moments and characters from the show. And there are so many great moments to choose from!
Person 2: Definitely. I think one of the most memorable moments for me was the "goodbye" scene between G'Kar and Londo in the episode "Objects at Rest." It was such a poignant and emotional moment, and it really showed how far their characters had come.
Person 1: Yes, that was a really powerful scene. It was great to see these two former enemies come together and find common ground. And it was a great way to wrap up their character arcs.
Person 2: Another memorable moment for me was the speech that Sheridan gives in "Severed Dreams." It's such an iconic moment in the show, and it really encapsulates the themes of the series.
Person 1: Yes, that speech is definitely one of the highlights of the series. It's so well-written and well-delivered, and it really captures the sense of hope and defiance that the show is all about.
Person 2: And speaking of great speeches, what did you think of the "Ivanova is always right" speech from "Moments of Transition"?
Person 1: Oh man, that speech gives me chills every time I watch it. It's such a powerful moment for Ivanova, and it really shows her strength and determination as a leader.
Person 2: Yes, that speech is definitely a standout moment for Ivanova's character. And it's just one example of the great writing and character development in the show.
Person 1: Absolutely. It's a testament to the talent of the writers and actors that they were able to create such rich and complex characters with so much depth and nuance.
Person 2: And it's not just the main characters that are well-developed, but also the supporting characters like Marcus, Zack, and Lyta. They all have their own stories and struggles, and they all contribute to the larger narrative in meaningful ways.
Person 1: Definitely. Babylon 5 is just such a well-rounded and satisfying show in every way. It's no wonder that it's still beloved by fans all these years later.
Person 2: Agreed. It's a show that has stood the test of time, and it will always hold a special place in my heart as one of my favorite TV shows of all time.
Person 1: One of the most interesting ethical dilemmas presented in Babylon 5 is the treatment of the Narn by the Centauri. What do you think about that storyline?
Person 2: Yeah, it's definitely a difficult issue to grapple with. On the one hand, the Centauri were portrayed as the aggressors, and their treatment of the Narn was brutal and unjust. But on the other hand, the show also presented some nuance to the situation, with characters like Londo and Vir struggling with their own complicity in the conflict.
Person 1: Exactly. I think one of the strengths of the show is its willingness to explore complex ethical issues like this. It's not just about good guys versus bad guys, but about the shades of grey in between.
Person 2: Yeah, and it raises interesting questions about power and oppression. The Centauri had more advanced technology and military might than the Narn, which allowed them to dominate and subjugate the Narn people. But at the same time, there were also political and economic factors at play that contributed to the conflict.
Person 1: And it's not just about the actions of the Centauri government, but also about the actions of individual characters. Londo, for example, was initially portrayed as a somewhat sympathetic character, but as the series progressed, we saw how his choices and actions contributed to the suffering of the Narn people.
Person 2: Yes, and that raises interesting questions about personal responsibility and accountability. Can an individual be held responsible for the actions of their government or their society? And if so, to what extent?
Person 1: That's a really good point. And it's also interesting to consider the role of empathy and compassion in situations like this. Characters like G'Kar and Delenn showed compassion towards the Narn people and fought against their oppression, while others like Londo and Cartagia were more indifferent or even sadistic in their treatment of the Narn.
Person 2: Yeah, and that raises the question of whether empathy and compassion are innate traits, or whether they can be cultivated through education and exposure to different cultures and perspectives.
Person 1: Definitely. And it's also worth considering the role of forgiveness and reconciliation. The Narn and Centauri eventually came to a sort of reconciliation in the aftermath of the Shadow War, but it was a difficult and painful process that required a lot of sacrifice and forgiveness on both sides.
Person 2: Yes, and that raises the question of whether forgiveness is always possible or appropriate in situations of oppression and injustice. Can the victims of such oppression ever truly forgive their oppressors, or is that too much to ask?
Person 1: It's a tough question to answer. I think the show presents a hopeful message in the end, with characters like G'Kar and Londo finding a measure of redemption and reconciliation. But it's also clear that the scars of the conflict run deep and that healing takes time and effort.
Person 2: Yeah, that's a good point. Ultimately, I think the show's treatment of the Narn-Centauri conflict raises more questions than it answers, which is a testament to its complexity and nuance. It's a difficult issue to grapple with, but one that's worth exploring and discussing.
Person 1: Let's switch gears a bit and talk about the character of Natasha Alexander. What did you think about her role in the series?
Person 2: I thought Natasha Alexander was a really interesting character. She was a tough and competent security officer, but she also had a vulnerable side and a complicated past.
Person 1: Yeah, I agree. I think she added a lot of depth to the show and was a great foil to characters like Garibaldi and Zack.
Person 2: And I also appreciated the way the show handled her relationship with Garibaldi. It was clear that they had a history and a lot of unresolved tension, but the show never made it too melodramatic or over-the-top.
Person 1: That's a good point. I think the show did a good job of balancing the personal drama with the larger political and sci-fi elements. And it was refreshing to see a female character who was just as tough and competent as the male characters.
Person 2: Definitely. I think Natasha Alexander was a great example of a well-written and well-rounded female character. She wasn't just there to be eye candy or a love interest, but had her own story and agency.
Person 1: However, I did feel like the show could have done more with her character. She was introduced fairly late in the series, and didn't have as much screen time as some of the other characters.
Person 2: That's true. I think the show had a lot of characters to juggle, and sometimes that meant some characters got sidelined or didn't get as much development as they deserved.
Person 1: And I also thought that her storyline with Garibaldi could have been developed a bit more. They had a lot of history and tension between them, but it felt like it was resolved too quickly and neatly.
Person 2: I can see where you're coming from, but I also appreciated the way the show didn't drag out the drama unnecessarily. It was clear that they both had feelings for each other, but they also had to focus on their jobs and the larger conflicts at play.
Person 1: I can see that perspective as well. Overall, I think Natasha Alexander was a great addition to the show and added a lot of value to the series. It's a shame we didn't get to see more of her.
Person 2: Agreed. But at least the show was able to give her a satisfying arc and resolution in the end. And that's a testament to the show's strength as a whole.
Person 1: One thing that really stands out about Babylon 5 is the quality of the special effects. What did you think about the show's use of CGI and other visual effects?
Person 2: I thought the special effects in Babylon 5 were really impressive, especially for a show that aired in the 90s. The use of CGI to create the spaceships and other sci-fi elements was really innovative for its time.
Person 1: Yes, I was really blown away by the level of detail and realism in the effects. The ships looked so sleek and futuristic, and the space battles were really intense and exciting.
Person 2: And I also appreciated the way the show integrated the visual effects with the live-action footage. It never felt like the effects were taking over or overshadowing the characters or the story.
Person 1: Absolutely. The show had a great balance of practical effects and CGI, which helped to ground the sci-fi elements in a more tangible and realistic world.
Person 2: And it's also worth noting the way the show's use of visual effects evolved over the course of the series. The effects in the first season were a bit rough around the edges, but by the end of the series, they had really refined and perfected the look and feel of the show.
Person 1: Yes, I agree. And it's impressive how they were able to accomplish all of this on a TV budget. The fact that the show was able to create such a rich and immersive sci-fi universe with limited resources is a testament to the talent and creativity of the production team.
Person 2: Definitely. And it's one of the reasons why the show has aged so well. Even today, the visual effects still hold up and look impressive, which is a rarity for a show that's almost 30 years old.
Person 1: Agreed. And it's also worth noting the way the show's use of visual effects influenced other sci-fi shows that came after it. Babylon 5 really set the bar for what was possible in terms of sci-fi visuals on TV.
Person 2: Yes, it definitely had a big impact on the genre as a whole. And it's a great example of how innovative and groundbreaking sci-fi can be when it's done right.
Person 1: Another character I wanted to discuss is Zathras. What did you think of his character?
Person 2: Zathras was a really unique and memorable character. He was quirky and eccentric, but also had a lot of heart and sincerity.
Person 1: Yes, I thought he was a great addition to the show. He added some much-needed comic relief, but also had some important moments of character development.
Person 2: And I appreciated the way the show used him as a sort of plot device, with his knowledge of time and space being instrumental in the resolution of some of the show's major storylines.
Person 1: Definitely. It was a great way to integrate a seemingly minor character into the larger narrative. And it was also interesting to see the different versions of Zathras from different points in time.
Person 2: Yeah, that was a clever storytelling device that really added to the sci-fi elements of the show. And it was also a great showcase for actor Tim Choate, who played the character with so much charm and energy.
Person 1: I also thought that Zathras was a great example of the show's commitment to creating memorable and unique characters. Even characters that only appeared in a few episodes, like Zathras or Bester, were given distinct personalities and backstories.
Person 2: Yes, that's a good point. Babylon 5 was really great at creating a diverse and interesting cast of characters, with each one feeling like a fully-realized and distinct individual.
Person 1: And Zathras was just one example of that. He was a small but important part of the show's legacy, and he's still remembered fondly by fans today.
Person 2: Definitely. I think his character is a great example of the show's ability to balance humor and heart, and to create memorable and beloved characters that fans will cherish for years to come.
"""


lines = conversation.lstrip('\n').rstrip('\n').split('\n')
for i in range(len(lines)):
  if lines[i].startswith('Person 1: '):
    key = 'my_user'
    message = lines[i].replace('Person 1: ', '')
  elif lines[i].startswith('Person 2: '):
    key = 'other_user'
    message = lines[i].replace('Person 2: ', '')
  else:
    print(lines[i])
    raise 'invalid line'  
  
  created_at = (now + timedelta(minutes=i)).isoformat()
  create_message( 
    client=ddb,
    message_group_uuid=message_group_uuid,
    created_at=created_at,
    message=message,
    my_user_uuid=users[key]['uuid'], # the values here are fetched from the database
    my_user_display_name=users[key]['display_name'], # the values here are fetched from the database
    my_user_handle=users[key]['handle'] # the values here are fetched from the database
  )

```

  - Running the script should show output like this.
![image](https://user-images.githubusercontent.com/56792014/227722056-ef669a1d-13be-47c3-bb29-21cf2b215166.png)




### 3. Implement Scan Script	

##### Context:
  - We will use a scan python script that will 


##### Steps:
  
  - Create a scan.py file inside the ddb folder.
  - Copy this code from week-5 branch

```
#!/usr/bin/env python3

import boto3
import sys

attrs = {
  'endpoint_url': 'http://localhost:8000'
}

ddb = boto3.resource('dynamodb',**attrs)
table_name='cruddur-messages'

table = ddb.Table(table_name)
response = table.scan()


items = response['Items']
for item in items:
    print(item)

```
  - type **chmod u+x ./bin/ddb/scan** to add the necessary permissions to run the script
  - Running this script will ensure that our seed data is successfully integrated with our schema.
  - Results should look like this, it shows that Andrew Brown and Andrew Bayko is conversing which is all pulled from the seed script.
![image](https://user-images.githubusercontent.com/56792014/227722966-49a90c75-bafa-4569-99ba-015db7db7cf1.png)



### 4. Implement Pattern Scripts for Read and List Conversations	

##### Context:
  - We will create a list-conversations and get-conversations python scrips inside a new folder called patterns which is inside the ddb folder. 
 

##### Steps:
  - Copy both the list-conversation and get-conversation from week-5 branch and paste them respectively on their created python files.

get-conversation.py
```
#!/usr/bin/env python3

import boto3
import sys
import json
import os
from datetime import datetime, timedelta, timezone

attrs = {
  'endpoint_url': 'http://localhost:8000'
}

if len(sys.argv) == 2:
  if "prod" in sys.argv[1]:
    attrs = {}

dynamodb = boto3.client('dynamodb',**attrs)
table_name = 'cruddur-messages'

message_group_uuid = "5ae290ed-55d1-47a0-bc6d-fe2bc2700399"

# define the query parameters
current_year = str(datetime.now().year)
query_params = {
  'TableName': table_name,
  'ScanIndexForward': False,
  'Limit': 20,
  'ReturnConsumedCapacity': 'TOTAL',
  'KeyConditionExpression': 'pk = :pk AND begins_with(sk,:year)',
  #'KeyConditionExpression': 'pk = :pk AND sk BETWEEN :start_date AND :end_date',
  'ExpressionAttributeValues': {
    ':year': {'S': (current_year)},
    #":start_date": { "S": "2023-03-01T00:00:00.000000+00:00" },
    #":end_date": { "S": "2023-03-19T23:59:59.999999+00:00" },
    ':pk': {'S': f"MSG#{message_group_uuid}"}
  }
}


# query the table
response = dynamodb.query(**query_params)

# print the items returned by the query
print(json.dumps(response, sort_keys=True, indent=2))

# print the consumed capacity
print(json.dumps(response['ConsumedCapacity'], sort_keys=True, indent=2))

items = response['Items']
items.reverse()

for item in items:
  sender_handle = item['user_handle']['S']
  message       = item['message']['S']
  timestamp     = item['sk']['S']
  dt_object = datetime.datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%S.%f%z')
  formatted_datetime = dt_object.strftime('%Y-%m-%d %I:%M %p')
  print(f'{sender_handle: <12}{formatted_datetime: <22}{message[:40]}...')
```


list-conversation
```
#!/usr/bin/env python3

import boto3
import sys
import json
import os
from datetime import datetime, timedelta, timezone

current_path = os.path.dirname(os.path.abspath(__file__))
parent_path = os.path.abspath(os.path.join(current_path, '..', '..', '..'))
sys.path.append(parent_path)
from lib.db import db

attrs = {
  'endpoint_url': 'http://localhost:8000'
}

if len(sys.argv) == 2:
  if "prod" in sys.argv[1]:
    attrs = {}

dynamodb = boto3.client('dynamodb',**attrs)
table_name = 'cruddur-messages'

def get_my_user_uuid():
  sql = """
    SELECT 
      users.uuid
    FROM users
    WHERE
      users.handle =%(handle)s
  """
  uuid = db.query_value(sql,{
    'handle':  'andrewbrown'
  })
  return uuid

my_user_uuid = get_my_user_uuid()
print(f"my-uuid: {my_user_uuid}")

current_year = datetime.now().year

# define the query parameters
query_params = {
  'TableName': table_name,
  'KeyConditionExpression': 'pk = :pk AND begins_with(sk,:year)',
  'ScanIndexForward': False,
  'ExpressionAttributeValues': {
    ':year': {'S': str(current_year) },
    ':pk': {'S': f"GRP#{my_user_uuid}"}
  },
  'ReturnConsumedCapacity': 'TOTAL'
}

# query the table
response = dynamodb.query(**query_params)

# print the items returned by the query
print(json.dumps(response, sort_keys=True, indent=2))
```

  - Add the **chmod u+x** to both python scripts
  - Results for list-conversations should look like this in the terminal
![image](https://user-images.githubusercontent.com/56792014/227723405-df371a30-b600-4a37-9e43-618650f7e933.png)


  - Results for get-conversations should look like this in the terminal. Shows how many messages are returned.
![image](https://user-images.githubusercontent.com/56792014/227723452-afab27ad-74ac-44fe-8b36-95f03e91da15.png)



### 5. Implement Update Cognito ID Script for Postgres Database	

##### Context:
  - We will be creating a new script that will update our database with the cognito user ids pulled from the **list-users.py** script. This will be called **update_cognito_users_id**
  - 


##### Steps:
  - Create a python file called **update_cognito_users_id** this will pull the user id from the list-users code and update the cognito_user_id in our db

```
#!/usr/bin/env python3

import boto3
import os
import sys

print("-- db-update-cognito-user-ids")

# due to the file structure of other scripts and folder locations, we will be needing to utilize the current_path and parent_path variables
current_path = os.path.dirname(os.path.abspath(__file__))
parent_path = os.path.abspath(os.path.join(current_path, '..', '..')) 
sys.path.append(parent_path)
from lib.db import db

# this will update the cognito user id within our RDS database

def update_users_with_cognito_user_id(handle,sub):
  sql = """
    UPDATE public.users
    SET cognito_user_id = %(sub)s
    WHERE
      users.handle = %(handle)s;
  """
  db.query_commit(sql,{
    'handle' : handle,
    'sub' : sub
  })

#this is the same as list_users script functionality which pulls the necessary data from the list of users

def get_cognito_user_ids():
  userpool_id = os.getenv("AWS_COGNITO_USER_POOL_ID")
  client = boto3.client('cognito-idp')
  params = {
    'UserPoolId': userpool_id,
    'AttributesToGet': [
        'preferred_username',
        'sub'
    ]
  }
  response = client.list_users(**params)
  users = response['Users']
  dict_users = {}
  for user in users:
    attrs = user['Attributes']
    sub    = next((a for a in attrs if a["Name"] == 'sub'), None)
    handle = next((a for a in attrs if a["Name"] == 'preferred_username'), None)
    dict_users[handle['Value']] = sub['Value']
  return dict_users


# this will iterate through data pulled from get_cognito_user_ids function and update the handle and sub attributes

users = get_cognito_user_ids()

for handle, sub in users.items():
  print('----',handle,sub)
  update_users_with_cognito_user_id(
    handle=handle,
    sub=sub
  )
```

  - End result should have an output like this.
![image](https://user-images.githubusercontent.com/56792014/227725485-64607fb9-56f2-4da3-a08f-38d1c3fe6e13.png)



### 6. Implement (Pattern A) Listing Messages in Message Group into Application	

##### Context:
  - We will modify and add various code changes to code base where the artificial conversation in our schema will be rendered by our cruddur app. 
  - Result should be like this
![image](https://user-images.githubusercontent.com/56792014/227724096-d15905d1-afc1-47cb-9fdf-4be4220bbb75.png)


##### Steps:
  - We will add a ddb.py file inside our lib folder. The contents of the ddb.py will be from the week-5 branch.
  - Add this function called **list_message_groups** in the ddb.py file.

```
 def list_message_groups(client,my_user_uuid):
    table_name = 'cruddur-messages'
    current_year = datetime.now().year
    query_params = {
      'TableName': table_name,
      'KeyConditionExpression': 'pk = :pk AND begins_with(sk,:year)',
      'ScanIndexForward': False,
      'Limit': 20,
      'ExpressionAttributeValues': {
        ':year': {'S': str(current_year) },
        ':pk': {'S': f"GRP#{my_user_uuid}"}
      }
    }
    print('query-params:', query_params)
    print(query_params)

    # query the table
    response = client.query(**query_params)
    items = response['Items']
    
    print('items:', items)

    results = []
    for item in items:
      last_sent_at = item['sk']['S']
      results.append({
        'uuid': item['message_group_uuid']['S'],
        'display_name': item['user_display_name']['S'],
        'handle': item['user_handle']['S'],
        'message': item['message']['S'],
        'created_at': last_sent_at
      })
    return results
```

  - We will create new folder called **cognito** in the bin folder. Inside the cognito folder we'll create a list-users python script.
  - This list-users.py script will allows us to get the user id of the users in our cognito pool that we will be using later.
  - We need to add a new variable in our docker-compose file in the backend-flask called $AWS_COGNITO_USER_POOL_ID in order for the script to work.

list-users.py
```
#!/usr/bin/env python3

import boto3
import os
import json


# This script will grab the attributes of users in the AWS COGNITO USER POOL indicated in the userpool_id
# Code snippet from https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/cognito-idp/client/list_users.html


userpool_id = os.getenv("AWS_COGNITO_USER_POOL_ID")
client = boto3.client('cognito-idp')

params = {
  'UserPoolId': userpool_id,
  'AttributesToGet': [
      'preferred_username',
      'sub'
  ]
}
response = client.list_users(**params)
print('------ response')
print(response)

users = response['Users']

print('------ users')
print(users)

print(json.dumps(users, sort_keys=True, indent=2, default=str))

dict_users = {}
for user in users:
  attrs = user['Attributes']
  sub    = next((a for a in attrs if a["Name"] == 'sub'), None)
  handle = next((a for a in attrs if a["Name"] == 'preferred_username'), None)
  dict_users[handle['Value']] = sub['Value']

# json.dumps arrange the data in a more readable format and grabs the key data which is 'sub' and 'preferred_username' for listing our users
print(json.dumps(dict_users, sort_keys=True, indent=2, default=str))
```

 
  - Navigate to app.py and go to **data_message_groups** function. This will be modified into the code below. Users are not hard coded but instead pulled from our database .

```
@app.route("/api/message_groups", methods=['GET'])
def data_message_groups():
  access_token = extract_access_token(request.headers)
  try:
      claims = cognito_jwt_token.verify(access_token)
      # authenticated request
      app.logger.debug('token is authenticated')
      cognito_user_id = claims['sub']
      model = MessageGroups.run(
        cognito_user_id=cognito_user_id
        )
      if model['errors'] is not None:
        return model['errors'], 422
      else:
        return model['data'], 200
 

  except TokenVerifyError as e:
       # unauthenticated request
      app.logger.debug(e)
      return {}, 401 # data = HomeActivities.run(logger=LOGGER) 
```

  - Navigate to **message_groups.py** in the services folder in backend-flask

message_groups.py
```
from datetime import datetime, timedelta, timezone

from lib.ddb import Ddb # importing ddb to find the handle from the uuid
from lib.db import db

class MessageGroups:
  def run(cognito_user_id):
    model = {
      'errors': None,
      'data': None
    }

    sql = db.template('users','uuid_from_cognito_user_id')
    my_user_uuid = db.query_value(sql,{
      'cognito_user_id': cognito_user_id
      })

    print(f"UUID:{my_user_uuid}")


    ddb = Ddb.client()
    data = Ddb.list_message_groups(ddb, my_user_uuid)
    print("list_message_groups:",data)
    model['data'] = data
    return model

```
  - We are importing ddb to find the handle from the 'uuid_from_handle'

![image](https://user-images.githubusercontent.com/56792014/227725868-be860133-c9e2-4ae2-8de1-e1b194d55ead.png)

  - Create a new folder under the **sql** folder called users. Create a sql file called **uuid_from_cognito_user_id**
  - This sql file will pull the uuid and store it in the sql variable.

uuid_from_cognito_user_id
```
SELECT 
    users.uuid
FROM public.users
WHERE
    users.cognito_user_id=%(cognito_user_id)s
LIMIT 1
```

  - We will also navigate to **MessageGroupsPage.js** and **MessageGroupPage.js** and add a Auth headers to our **loadData** and **loadMessageGroupData**,**loadMessageGroupsData** variable respectively.
```
 headers: {
          'Authorization': `Bearer ${localStorage.getItem("access_token")}`
```

  - MessageForm.js will also be modified to add the Auth Header indicated above.
![image](https://user-images.githubusercontent.com/56792014/227726410-a803e3b0-6d92-43bb-83e4-bd1c341ed47a.png)

  - We will also create a file called checkAuth.js for reusability. This will be contained in the ./frontend-react-js/src/lib/checkAuth
  - After creating the folder and the file. Copy the checkAuth function from the HomeFeedPage.js
  
```
import { Auth } from 'aws-amplify';

// check if we are authenticated
const checkAuth = async (setUser) => {
    Auth.currentAuthenticatedUser({
      // Optional, By default is false. 
      // If set to true, this call will send a 
      // request to Cognito to get the latest user data
      bypassCache: false 
    })
    .then((user) => {
      console.log('user',user);
      return Auth.currentAuthenticatedUser()
    }).then((cognito_user) => {
        setUser({
          display_name: cognito_user.attributes.name,
          handle: cognito_user.attributes.preferred_username
        })
    })
    .catch((err) => console.log(err));
  };

export default checkAuth;
```

  - This function will be currently be exported to **HomeFeedPage.js MessageGroupPage.js MessageGroupsPage.js** and any other files that will be using checkAuth function.

  - Add a $AWS_ENDPOINT_URL in our docker-compose file and point it to our local dynamodb **http://dynamodb-local:8000**
![image](https://user-images.githubusercontent.com/56792014/227726973-214255de-7939-402c-9921-ec97f481b77c.png)

  - End result should look like this
![image](https://user-images.githubusercontent.com/56792014/227727000-150938af-638e-4150-be7e-44c1e3ee0167.png)


### 7. Implement (Pattern B) Listing Messages Group into Application	

##### Context:

  - We need to pass a message_group_uuid for each conversation created in the messages section as to uniquely identify the conversations.


##### Steps:
  - Modify the path section of MessageGroupPage in app.js
  - ![image](https://user-images.githubusercontent.com/56792014/227727165-18858c14-818d-40ee-92ee-cd723f4f95dc.png)
  
  - MessageGroupPage.js backend_url variable will also be modified to pull from the **params.message_group_uuid**
  ![image](https://user-images.githubusercontent.com/56792014/227727246-0dedcad4-39f5-40fd-9a77-b7c7238e49b7.png)

  - Navigate to MessageGroupItem.js and we will add modifications to the **classes** function and to the classes html link.
![image](https://user-images.githubusercontent.com/56792014/227727922-c5fcbeb1-3b97-4d89-a7ab-5d0d00692904.png)

  - End result should show the message_group_uuid displaying in the link
  ![image](https://user-images.githubusercontent.com/56792014/227728012-3db6695a-3cc3-435a-9829-7239a00b481f.png)



### 8. Implement (Pattern C) Creating a Message for an existing Message Group into Application	

##### Context:
  - We need to hook up other parts of our application that makes up the creation of messages and rendering of messages from our database into the application


##### Steps:
  
  - Modify the /api/messages/@<string:handle> app.route into the code below.

app.py
```
@app.route("/api/messages/<string:message_group_uuid>", methods=['GET'])
def data_messages(message_group_uuid): 
  access_token = extract_access_token(request.headers)
  try:
    claims = cognito_jwt_token.verify(access_token)
    app.logger.debug('token is authenticated')
    cognito_user_id = claims['sub']
    model = Messages.run(
      cognito_user_id=cognito_user_id,
      message_group_uuid=message_group_uuid
    )
    if model['errors'] is not None:
      return model['errors'], 422
    else:
      return model['data'], 200

  except TokenVerifyError as e:
      # unauthenticated request
      app.logger.debug(e)
      return {}, 401
```

  - Navigate to messages.py and add the code modifications from week-5 branch 
  
messages.py
```
from datetime import datetime, timedelta, timezone
from lib.ddb import Ddb
from lib.db import db

class Messages:
  def run(message_group_uuid,cognito_user_id):
    model = {
      'errors': None,
      'data': None
    }

    sql = db.template('users','uuid_from_cognito_user_id')
    my_user_uuid = db.query_value(sql,{
      'cognito_user_id': cognito_user_id
      })

    print(f"UUID: {my_user_uuid}")  

    # TODO: we're suppose to check that we have permission to access
    # this message_group_uuid, its missing in our access pattern.

    ddb = Ddb.client()
    data = Ddb.list_messages(ddb, message_group_uuid)
    print(" --------list_messages")
    print(data)

    model['data'] = data
    return model 
```
  
  - Add the list_message function from the week-5 dbb.py file to my ddb.py file

```
def list_messages(client,message_group_uuid):
    current_year = datetime.now().year
    table_name = 'cruddur-messages'
    query_params = {
      'TableName': table_name,
      'KeyConditionExpression': 'pk = :pk AND begins_with(sk,:year)',
      'ScanIndexForward': False,
      'Limit': 20,
      'ExpressionAttributeValues': {
        ':year': {'S': str(current_year) },
        ':pk': {'S': f"MSG#{message_group_uuid}"}
      }
    }


    # query the table
    response = client.query(**query_params)
    items = response['Items']
    items.reverse()
    results = []

    for item in items:
      last_sent_at = item['sk']['S']
      results.append({
        'uuid': item['message_uuid']['S'],
        'display_name': item['user_display_name']['S'],
        'handle': item['user_handle']['S'],
        'message': item['message']['S'],
        'created_at': last_sent_at
      })
    return results
```

  - End results should load the messages when clicking on the message conversations in the side. 
![image](https://user-images.githubusercontent.com/56792014/227730696-f29cd990-d56a-4137-8695-37820cc3919e.png)



### 9. Implement (Pattern D) Creating a Message for a new Message Group into Application	

##### Context:
  - Create and send a new message in a conversation
 

##### Steps:
  - **MessageForm.js** onsubmit function will be modified

  - The condition in the attached screenshot accords to the access patterns between **Pattern C** which is the **creation of a new conversation** vs **Pattern D** which **updates an existing conversation**. 
![image](https://user-images.githubusercontent.com/56792014/227729673-ab27db4c-c316-4d01-8357-e6acae8941ac.png)

  - Access patterns C & D
![image](https://user-images.githubusercontent.com/56792014/227729796-3a7578ab-3251-40f3-ae03-f58e02a265c4.png)

  - The **app.route(/api/messages)** section will be modified to take the message_group_uuid and run the CreateMessage mode **update** or **create** depending if creating a new conversation or updating an existing conversation
  
```
@app.route("/api/messages", methods=['POST','OPTIONS'])
@cross_origin()
def data_create_message():
  access_token = extract_access_token(request.headers)
  user_receiver_handle = request.json.get('handle',None)
  message_group_uuid = request.json.get('message_group_uuid',None)
    
  try:
    claims = cognito_jwt_token.verify(access_token)
    app.logger.debug('token is authenticated')
    app.logger.debug(claims)
    cognito_user_id = claims['sub']
    message = request.json['message']
    
    if message_group_uuid == None:
      # Create for the first time
      model = CreateMessage.run(
        mode="create",
        message=message,
        cognito_user_id=cognito_user_id,
        user_receiver_handle=user_receiver_handle
      )
    else:
      # Push onto existing Message Group
      model = CreateMessage.run(
        mode="update",
        message=message,
        message_group_uuid=message_group_uuid,
        cognito_user_id=cognito_user_id
      )
    
    if model['errors'] is not None:
      return model['errors'], 422
    else:
      return model['data'], 200

  except TokenVerifyError as e:
      # unauthenticated request
      app.logger.debug(e)
      return {}, 401
```


```
 const onsubmit = async (event) => {
    event.preventDefault();
    try {
      const backend_url = `${process.env.REACT_APP_BACKEND_URL}/api/messages`
      console.log('onsubmit payload', message)
      let json = { 'message': message }
      if (params.handle) {
        json.handle = params.handle
      } else {
        json.message_group_uuid = params.message_group_uuid
      }

      const res = await fetch(backend_url, {
        method: "POST",
        headers: {
          'Authorization': `Bearer ${localStorage.getItem("access_token")}`,
          'Accept': 'application/json',
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(json)
      });
      let data = await res.json();
      if (res.status === 200) {
        console.log('data:',data)
        if (data.message_group_uuid) {
          console.log('redirect to message group')
          window.location.href = `/messages/${data.message_group_uuid}`
        } else {
          props.setMessages(current => [...current,data]);
        }
      } else {
        console.log(res)
      }
    } catch (err) {
      console.log(err);
    }
  }

```

  - Go to week-5 branch and get the create_message.py code and paste it into our create_message.py file

create_message.py
```
from datetime import datetime, timedelta, timezone
from lib.db import db
from lib.ddb import Ddb


class CreateMessage:
  # mode indicates if we want to create a new message_group or using an existing one
  def run(mode, message, cognito_user_id, message_group_uuid=None, user_receiver_handle=None):
    model = {
      'errors': None,
      'data': None
    }

    if (mode == "update"):
      if message_group_uuid == None or len(message_group_uuid) < 1:
        model['errors'] = ['message_group_uuid_blank']


    if cognito_user_id == None or len(cognito_user_id) < 1:
      model['errors'] = ['cognito_user_id_blank']

    if (mode == "create"):
      if user_receiver_handle == None or len(user_receiver_handle) < 1:
        model['errors'] = ['user_receiver_handle_blank']

    if message == None or len(message) < 1:
      model['errors'] = ['message_blank'] 
    elif len(message) > 1024:
      model['errors'] = ['message_exceed_max_chars'] 

    if model['errors']:
      # return what we provided
      model['data'] = {
        'display_name': 'Andrew Brown',
        'handle':  user_sender_handle,
        'message': message
      }
    else:
      sql = db.template('users','create_message_users')

      if user_receiver_handle == None:
        rev_handle = ''
      else:
        rev_handle = user_receiver_handle
      users = db.query_array_json(sql,{
        'cognito_user_id': cognito_user_id,
        'user_receiver_handle': rev_handle
      })
      
      my_user    = next((item for item in users if item["kind"] == 'sender'), None)
      other_user = next((item for item in users if item["kind"] == 'recv')  , None)

      print("USERS =-=-=-=-==")
      print("USERS=[my-user]=========")
      print(my_user)
      print("USERS=[other-user]======")
      print(other_user)

      ddb = Ddb.client()

      if (mode == "update"):
        data = Ddb.create_message(
          client=ddb,
          message_group_uuid=message_group_uuid,
          message=message,
          my_user_uuid=my_user['uuid'],
          my_user_display_name=my_user['display_name'],
          my_user_handle=my_user['handle']
        )
      elif (mode == "create"):
        data = Ddb.create_message_group(
          client=ddb,
          message=message,
          my_user_uuid=my_user['uuid'],
          my_user_display_name=my_user['display_name'],
          my_user_handle=my_user['handle'],
          other_user_uuid=other_user['uuid'],
          other_user_display_name=other_user['display_name'],
          other_user_handle=other_user['handle']
        )
      model['data'] = data
      return model
```

  - Navigate again to week-5 branch and get the create_message function code from the ddb.py file and paste it into our ddb.py file.

ddb.py create_message function
```
 def create_message(client, message_group_uuid, message, my_user_uuid, my_user_display_name, my_user_handle):
    now = datetime.now(timezone.utc).astimezone().isoformat()
    created_at = now
    message_uuid = str(uuid.uuid4())

    record = {
      'pk':   {'S': f"MSG#{message_group_uuid}"},
      'sk':   {'S': created_at },
      'message': {'S': message},
      'message_uuid': {'S': message_uuid},
      'user_uuid': {'S': my_user_uuid},
      'user_display_name': {'S': my_user_display_name},
      'user_handle': {'S': my_user_handle}
    }
    # insert the record into the table
    table_name = 'cruddur-messages'
    response = client.put_item(
      TableName=table_name,
      Item=record
    )
    # print the response
    print('----------this is the ddb response')
    print(response)
    print(record)
    return {
      'message_group_uuid': message_group_uuid,
      'uuid': my_user_uuid,
      'display_name': my_user_display_name,
      'handle':  my_user_handle,
      'message': message,
      'created_at': created_at
    }
```

  - Results for updating an existing conversation should look like this.
![image](https://user-images.githubusercontent.com/56792014/227730409-d4312228-7b7c-4ca4-9245-b806b87d3c57.png)

  
  - We will now proceed on the implementation of new messages creation
  - Navigate to App.js and insert a new path 

**App.js**
![image](https://user-images.githubusercontent.com/56792014/227730830-1a58ff1a-945f-49c9-8071-acab8fd08c4b.png)
![image](https://user-images.githubusercontent.com/56792014/227730843-ea682cc9-aff7-42f4-97c0-b1836128577f.png)


  - Grab the file called MessageGroupNewPage.js from week-5 branch and put it in our pages folder. Add the corresponding routing from the affected pages and add the CheckAuth to the new files.

**MessageGroupNewPage.js**
![image](https://user-images.githubusercontent.com/56792014/227731131-47a20c83-34b2-4be9-b036-ee0accfa9d18.png)

  - Add a new user in our seed.sql to test our create new message functionality

seed.sql
![image](https://user-images.githubusercontent.com/56792014/227731171-7b70eeab-6d47-4862-9bd4-e0390cd5f293.png)

  - For the meantime we will add this user right now after adding it to our seed.sql

Login to our database 
```
./bin/db/connect
```

Insert the new user manually in our existing database
```
INSERT INTO public.users (display_name,email, handle, cognito_user_id) VALUES ('Londo Mollari', 'lmollari@centari.com', 'londo','MOCK');
```

  - From app.py we will add a new route call user_shorts
![image](https://user-images.githubusercontent.com/56792014/227731310-a4ab3f61-eb75-4636-a680-c5b41ff297f8.png)

  - And also add this new route in our app.py
![image](https://user-images.githubusercontent.com/56792014/227731333-ab3bebe8-f7db-49ef-a8c2-8301b15a7db2.png)

  - We will also create a new file in our services folder called **users_short.py**. The contents are from the week-5 branch
![image](https://user-images.githubusercontent.com/56792014/227731354-4eff55fd-d00d-475b-a9c2-3bdf66549945.png)

  - We will also create a new file called **MessageGroupNewItem.js** and add it to our components folder
![image](https://user-images.githubusercontent.com/56792014/227731457-03e3c719-bbbb-4eed-9ca6-3f3b3f7ead9f.png)


  - All of the newly added files will enable the app to use the handle as an endpoint to create a new message
  - End result should look like this
![image](https://user-images.githubusercontent.com/56792014/227731511-491319ed-6695-4dc9-bef5-a4f7e6b78540.png)




### 10. Implement (Pattern E) Updating a Message Group using DynamoDB Streams	

##### Context:
  - Leverage DynamoDB Streams to our creation of new conversations and updating existing conversations
  
DynamoDB Modeling
![image](https://user-images.githubusercontent.com/56792014/227732101-2f108a4a-0d3b-40ad-b765-a9dc62e88e34.png)


##### Steps:

  - Copy the file **cruddur-messaging-stream.py** from branch week-5 again again and put it in the lambdas folder. We will create a new lambda using this code.
  - Navigate to AWS Console and go to AWS Lambda
  - Click on 'Create function'
  ![image](https://user-images.githubusercontent.com/56792014/227732380-15b9f8df-491e-4618-9d9c-2dabbeba877e.png)

  - Configure the Lambda after creation by navigating to **Configuration > VPC** and setting up the VPC
  - Also configure the necessary permissions to allow access to DynamoDB
  ![image](https://user-images.githubusercontent.com/56792014/227732514-d2db1295-21d0-4f01-9f89-8c1e726a02f0.png)
  ![image](https://user-images.githubusercontent.com/56792014/227732531-7e6f0073-a4a4-4eba-932f-e35637a143c6.png)

  - Comment out the endpoint url to allow the DynamoDB Streams to access the application
  ![image](https://user-images.githubusercontent.com/56792014/227732581-83911e21-02ba-4eff-bbbe-77563c2c3729.png)

  - schema-load in ddb folder will be modified to include a **GlobalSecondaryIndex**

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
  - After updating schema-load file
  - Run the schema-load file with "prod" at the end to trigger the dynamodb streams instead of the local dynamodb


  - End result should look like this
![image](https://user-images.githubusercontent.com/56792014/227732172-df19a970-30c5-44be-a9f5-6407a48d2c8d.png)

  - Cloudwatch Logs 
![image](https://user-images.githubusercontent.com/56792014/227732820-37dcc92c-b23d-4974-8c24-d34b729d81b7.png)
