# superlaser
This is a Real-Time Market Order Book &amp; VWAP Engine.
This project is just for fun - my brain was too idle, so I asked Gemini for project ideas.
At the moment, I'm just doing this localy on a KinD cluster, but eventually I'll want to scale this to EKS or something that could be used in a production system. 


## Local Dev
### Architecture
#### Cluster
I used a local [KinD (Kubernetes in Docker)](https://kind.sigs.k8s.io/) cluster using the 
`kindest/node:v1.33.12` node image.

#### Ingestion Service
A python service that will subscribe to a Coinbase Advanced API channel for live market data.

### Deployment
#### Spin up the infra
```bash
cd infra/
terrafor init
terraform plan -out "plan"
terraform apply "plan"  # May require sudo for KinD
```

## Design Choices / Thoughts
### Ingestion Service
- Not sure how worth it it is, but I want to test what would be faster - manually creating JWT's and signing my messages to Coinbase's Advanced Trade API vs using the CDP SDK.
  On one hand, although good to learn, it does suck to write that boiler plate code since it feels like bad practice. On the other hand, importing the SDK will also import a ton
  of Web3 bloat that I simply will not need. If the project expands to need that, I can always make another separate service. For now, I will stick to the manual route.
- Now the issue is how do I toggle the ingestion service? Yes, it could automatically subscribe to the feed, but how would I unsubscribe? I could make it a webservice with FastAPI
  or something, but this seems rather bloated. I'm thinking of having it unsubscribe on SIGTERM, which is how k8s will destroy the container. If I need to communicate with the
  service in more ways, I could probably add signal handlers and make a cli that sends signals via kubectl. I do not imagine the user will interact much with this service.
  **Decision: I won't even unsubscribe, but I'll rely on the server automatically closing my connection after the heartbeats stop coming in.**

