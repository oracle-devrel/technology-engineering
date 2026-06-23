Vom Skript zum Terraform .tftpl Template file:
:%s/\$/${DOLLAR}/g
dann die von Terraform einzusetzenden Strings durch z.B. ${tf_compartment_id} ersetzen.

Vom Terraform Template zum Skript:
:%s/\${DOLLAR}/$/g

Beispiel für das Rendering von derart vorbereiteten Templates
Beachte die Zeile DOLLAR = "$"
locals {
  user-setup_bash = templatefile("./InstanceScripts/user-setup.bash.tftpl", {
    tf_eternal_terminal_nsg = "EternalTerminal"
    tf_http_nsg             = "HTTP"
    DOLLAR = "$"
  })
}

resource "local_file" "user-setup_bash" {
  content = local.user-setup_bash
  filename = "./InstanceScripts/user-setup.bash"
}
