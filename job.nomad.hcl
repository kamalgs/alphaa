job "alphaa" {
  datacenters = ["dc1"]
  type        = "service"

  group "app" {
    count = 0

    network {
      mode = "host"
    }

    task "alphaa" {
      driver = "docker"

      config {
        image        = "alphaa:latest"
        network_mode = "host"
      }

      resources {
        cpu    = 500
        memory = 512
      }
    }
  }
}
