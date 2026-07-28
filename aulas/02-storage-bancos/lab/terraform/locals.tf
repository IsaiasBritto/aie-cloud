locals {
  location_sql    = coalesce(var.location_sql, var.location)
  location_search = coalesce(var.location_search, var.location)
  location_aci    = coalesce(var.location_aci, var.location)
  image_prefix    = var.registry_server == null ? "" : "${var.registry_server}/"
}

