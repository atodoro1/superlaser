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

## Design Choices
### Ingestion Service
- Not sure how worth it it is, but I want to test what would be faster - manually creating JWT's and signing my messages to Coinbase's Advanced Trade API vs using the CDP SDK.
  On one hand, although good to learn, it does suck to write that boiler plate code since it feels like bad practice. On the other hand, importing the SDK will also import a ton
  of Web3 bloat that I simply will not need. If the project expands to need that, I can always make another separate service. For now, I will stick to the manual route.
