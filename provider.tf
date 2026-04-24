terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 7.0"
    }
  }
  # NO backend block here — uses local state intentionally
}

provider "google" {
  project = var.project_id
  region  = var.region
}
