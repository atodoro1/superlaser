resource "kind_cluster" "cluster" {
  name       = "superlaser-cluster"
  node_image = "kindest/node:v1.33.12"
}

