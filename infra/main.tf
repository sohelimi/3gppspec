terraform {
  required_providers {
    google = { source = "hashicorp/google", version = "~> 5.0" }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# ── Artifact Registry (store Docker images) ───────────────────────────────────
resource "google_artifact_registry_repository" "gppspec" {
  location      = var.region
  repository_id = "3gppspec"
  format        = "DOCKER"
  description   = "3gppSpec 3GPP chatbot images"
}

# ── Secret Manager (Gemini API key) ───────────────────────────────────────────
resource "google_secret_manager_secret" "gemini_api_key" {
  secret_id = "gemini-api-key"
  replication { auto {} }
}

# ── Cloud Run service ─────────────────────────────────────────────────────────
resource "google_cloud_run_v2_service" "gppspec" {
  name     = "3gppspec"
  location = var.region

  template {
    containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/3gppspec/3gppspec:latest"

      ports { container_port = 8080 }

      resources {
        limits = { memory = "2Gi", cpu = "2" }
        startup_cpu_boost = true
      }

      env {
        name = "GEMINI_API_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.gemini_api_key.secret_id
            version = "latest"
          }
        }
      }

      env { name = "APP_ENV",        value = "production" }
      env { name = "CHROMA_DB_PATH", value = "/app/data/chromadb" }
      env {
        name  = "ALLOWED_ORIGINS"
        value = "https://3gpp.deltatechus.com"
      }
    }

    scaling { min_instance_count = 0, max_instance_count = 2 }
  }

  traffic { type = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST", percent = 100 }
}

# ── Allow public access ───────────────────────────────────────────────────────
resource "google_cloud_run_service_iam_member" "public" {
  location = google_cloud_run_v2_service.gppspec.location
  service  = google_cloud_run_v2_service.gppspec.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# ── Custom domain mapping ─────────────────────────────────────────────────────
resource "google_cloud_run_domain_mapping" "gppspec" {
  location = var.region
  name     = "3gpp.deltatechus.com"

  metadata { namespace = var.project_id }
  spec { route_name = google_cloud_run_v2_service.gppspec.name }
}
