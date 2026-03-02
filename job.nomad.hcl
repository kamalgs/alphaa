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
        image        = "alphaa:local"
        network_mode = "host"
      }

      env {
        OTEL_SERVICE_NAME                = "alphaa"
        OTEL_EXPORTER_OTLP_ENDPOINT      = "http://localhost:4318"
        OTEL_EXPORTER_OTLP_PROTOCOL      = "http/protobuf"
        OTEL_LOGS_EXPORTER               = "otlp"
        OTEL_METRICS_EXPORTER            = "otlp"
        OTEL_TRACES_EXPORTER             = "otlp"
        OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED = "true"
      }

      resources {
        cpu    = 500
        memory = 512
      }
    }
  }
}
