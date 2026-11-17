run "reject_empty_applications" {
  command = plan
  module { source = "./modules/application-config" }
  variables { applications = [] }
  expect_failures = [var.applications]
}

run "reject_empty_components" {
  command = plan
  module { source = "./modules/application-config" }
  variables { applications = [{ name = "shop", components = [] }] }
  expect_failures = [var.applications]
}

run "reject_duplicate_applications" {
  command = plan
  module { source = "./modules/application-config" }
  variables {
    applications = [{ name = "shop", components = [{ name = "invoice" }] }, { name = "shop", components = [{ name = "checkout" }] }]
  }
  expect_failures = [var.applications]
}

run "reject_duplicate_components" {
  command = plan
  module { source = "./modules/application-config" }
  variables {
    applications = [{ name = "shop", components = [{ name = "invoice" }] }, { name = "orders", components = [{ name = "invoice" }] }]
  }
  expect_failures = [var.applications]
}

run "reject_unsafe_component_name" {
  command = plan
  module { source = "./modules/application-config" }
  variables { applications = [{ name = "shop", components = [{ name = "../invoice" }] }] }
  expect_failures = [var.applications]
}

run "reject_unsafe_build_path" {
  command = plan
  module { source = "./modules/application-config" }
  variables { applications = [{ name = "shop", components = [{ name = "invoice", build_spec_path = "../bad.yaml" }] }] }
  expect_failures = [var.applications]
}

run "reject_managed_build_path_collision" {
  command = plan
  module { source = "./modules/application-config" }
  variables { applications = [{ name = "shop", components = [{ name = "invoice", build_spec_path = "shop-package-pipeline.yaml" }] }] }
  expect_failures = [var.applications]
}

run "legacy_json_remains_supported" {
  command = plan
  module { source = "./modules/application-config" }
  variables { applications = "[{\"name\":\"shop\",\"components\":[{\"name\":\"invoice\"}]}]" }
  assert {
    condition     = jsondecode(output.applications)[0].components[0].name == "invoice"
    error_message = "Legacy JSON must remain accepted."
  }
}
