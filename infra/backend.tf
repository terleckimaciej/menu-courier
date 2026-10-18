# The bucket is created manually (see README.md): Terraform cannot store its
# state in a bucket it has yet to create. Backend blocks do not accept variables.
terraform {
  backend "gcs" {
    bucket = "menu-courier-511718-tfstate"
    prefix = "menu-courier"
  }
}
