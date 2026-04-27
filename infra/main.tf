terraform {
  required_providers {
    google = { source = "hashicorp/google", version = "~> 5.0" }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# ── Artifact Registry ─────────────────────────────────────────────────────────
resource "google_artifact_registry_repository" "gppspec" {
  location      = var.region
  repository_id = "gppspec"
  format        = "DOCKER"
  description   = "3gppSpec 3GPP chatbot images"
}

# ── Secret Manager (Groq API key) ─────────────────────────────────────────────
resource "google_secret_manager_secret" "groq_api_key" {
  secret_id = "groq-api-key"

  replication {
    auto {}
  }
}

# ── GCS bucket for ChromaDB ───────────────────────────────────────────────────
resource "google_storage_bucket" "chromadb" {
  name          = "gppspec-chromadb"
  location      = var.region
  force_destroy = false

  uniform_bucket_level_access = true
}

# ── Cloud Run service account ─────────────────────────────────────────────────
resource "google_service_account" "cloudrun_sa" {
  account_id   = "gppspec-cloudrun"
  display_name = "3gppSpec Cloud Run"
}

resource "google_storage_bucket_iam_member" "chromadb_reader" {
  bucket = google_storage_bucket.chromadb.name
  role   = "roles/storage.objectViewer"
  member = "serviceAccount:${google_service_account.cloudrun_sa.email}"
}

resource "google_secret_manager_secret_iam_member" "groq_secret_access" {
  secret_id = google_secret_manager_secret.groq_api_key.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.cloudrun_sa.email}"
}

# ── Cloud Run service ─────────────────────────────────────────────────────────
resource "google_cloud_run_v2_service" "gppspec" {
  name     = "gppspec"
  location = var.region

  template {
    service_account = google_service_account.cloudrun_sa.email

    volumes {
      name = "chromadb"
      gcs {
        bucket    = google_storage_bucket.chromadb.name
        read_only = true
      }
    }

    containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/gppspec/gppspec:latest"

      ports {
        container_port = 8080
      }

      resources {
        limits = {
          memory = "4Gi"
          cpu    = "2"
        }
        startup_cpu_boost = true
      }

      volume_mounts {
        name       = "chromadb"
        mount_path = "/data"
      }

      env {
        name = "GROQ_API_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.groq_api_key.secret_id
            version = "latest"
          }
        }
      }

      env {
        name  = "APP_ENV"
        value = "production"
      }

      env {
        name  = "CHROMA_DB_PATH"
        value = "/data/chromadb"
      }

      env {
        name  = "ALLOWED_ORIGINS"
        value = "https://3gpp.deltatechus.com"
      }
    }

    scaling {
      min_instance_count = 0
      max_instance_count = 2
    }

    # Allow long timeout for ChromaDB initialization from GCS on cold start
    timeout = "300s"
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }

  depends_on = [
    google_storage_bucket_iam_member.chromadb_reader,
    google_secret_manager_secret_iam_member.groq_secret_access,
  ]
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

  metadata {
    namespace = var.project_id
  }

  spec {
    route_name = google_cloud_run_v2_service.gppspec.name
  }
}
