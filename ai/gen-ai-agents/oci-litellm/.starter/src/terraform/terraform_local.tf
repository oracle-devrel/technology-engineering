terraform {
  backend "local" { 
    path = "../../target/terraform.tfstate" 
  }
}