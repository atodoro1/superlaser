# superlaser
This is a Real-Time Market Order Book &amp; VWAP Engine.
This project is just for fun - my brain was too idle, so I asked Gemini for project ideas.

## Architecture
### Cluster
I used a local [KinD (Kubernetes in Docker)](https://kind.sigs.k8s.io/) cluster using the 
`kindest/node:v1.33.12` node image.

## 1) Spin up the infra
```bash
cd infra/
terrafor init
terraform plan -out "plan"
terraform apply "plan"  # May require sudo for KinD
```
