
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

resource "google_storage_bucket" "infra" {
  name          = "infra"
  location      = "US-CENTRAL1"
  force_destroy = true
  uniform_bucket_level_access = true
}