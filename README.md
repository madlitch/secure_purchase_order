# StringShare

## Description

StringShare is a distributed social media network where anyone can create a StringShare instance for their own
community, while all StringShare instances communicate with each other to form a larger distributed network.

## Run

### To run this project with both the _stringshare.ca_ and _ontariotechu.ca_ instances:

1. Clone this repository into two separate directories (e.g. /stringshare and /stringshare-otu)

2. To run the _stringshare.ca_ instance (run in respective directory):

   On first run: ```docker compose up --build```

   Afterwards: ```docker compose up```

3. To run the _ontariotechu.ca_ instance (run in respective directory):

   On first run: ```docker compose -f docker-compose-ontariotechu.yaml up --build```

   Afterwards: ```docker compose -f docker-compose-ontariotechu.yaml up```
   
### Using the StringShare API Directly

1. Once the servers are running, go to http://localhost:8080/docs (stringshare.ca) and http://localhost:8081/docs (ontariotechu.ca)
   for API documentation and endpoints
2. Execute the '/reset_database' endpoint in both to init the database with mock data
3. Click the 'Authorize' button in the top right, and log in using any of the usernames (you can find them in the `app/data/{COMMUNITY}/users.sql` file)

The servers will take a few seconds to start. If they don't, you can manually start them in the Docker desktop app.

### Using the StringShare Mobile App

Once the servers are running, you can run the mobile apps and connect: https://github.com/DaanyaalTahir/string-share


