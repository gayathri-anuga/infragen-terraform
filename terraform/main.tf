terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = "project-5fbed52e-54fb-4c84-ba3"
  region  = "us-central1"
}

resource "google_project_service" "run-api" {
  service = "run.googleapis.com"
}

resource "google_cloud_run_service" "infragen-service" {
  depends_on = [
    google_project_service.run-api
  ]
  name     = "infragen-service"
  location = "us-central1"
  template {
    spec {
      containers {
        image = "gcr.io/cloudrun/hello"
        ports {
          container_port = 8080
        }
      }
    }
  }
  traffic {
    percent         = 100
    latest_revision = true
  }
}