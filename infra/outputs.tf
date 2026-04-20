output "cloud_run_url" {
  value       = google_cloud_run_v2_service.gppspec.uri
  description = "Cloud Run service URL (before custom domain)"
}

output "custom_domain" {
  value       = "https://3gpp.deltatechus.com"
  description = "Production URL after DNS CNAME is configured"
}
