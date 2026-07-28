terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.100"
    }
  }
}

provider "azurerm" {
  features {}
}

# Tags aplicadas a todos os recursos (paridade com a VM criada no portal)
locals {
  tags = {
    aula         = "1"
    disciplina   = "cloud-cognitive"
    provisionado = "terraform"
  }
}

# Resource Group provisionado via Terraform (separado do rg-lab-aula01 da Atividade 4,
# para podermos comparar a MESMA VM criada nas duas formas: portal vs IaC)
resource "azurerm_resource_group" "rg" {
  name     = var.resource_group_name
  location = var.location
  tags     = local.tags
}

# ---------------------------------------------------------------------------
# Rede — equivalente Terraform do template ARM exportado em ../../template/
# VNet 10.0.0.0/16 com subnet "default" 10.0.0.0/24
# ---------------------------------------------------------------------------
resource "azurerm_virtual_network" "vnet" {
  name                = "vm-lab-aula01-vnet"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  address_space       = ["10.0.0.0/16"]
  tags                = local.tags
}

resource "azurerm_subnet" "default" {
  name                 = "default"
  resource_group_name  = azurerm_resource_group.rg.name
  virtual_network_name = azurerm_virtual_network.vnet.name
  address_prefixes     = ["10.0.0.0/24"]
}

# NSG com as 3 regras inbound do template (SSH 22, HTTPS 443, HTTP 80)
resource "azurerm_network_security_group" "nsg" {
  name                = "vm-lab-aula01-nsg"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  tags                = local.tags

  security_rule {
    name                       = "SSH"
    priority                   = 300
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "22"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }

  security_rule {
    name                       = "HTTPS"
    priority                   = 320
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "443"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }

  security_rule {
    name                       = "HTTP"
    priority                   = 340
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "80"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }
}

# IP público estático (SKU Standard, como no template)
resource "azurerm_public_ip" "pip" {
  name                = "vm-lab-aula01-ip"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  allocation_method   = "Static"
  sku                 = "Standard"
  tags                = local.tags
}

# NIC com Accelerated Networking (suportado pelo D2s_v3) e o IP público anexado
resource "azurerm_network_interface" "nic" {
  name                          = "vm-lab-aula01-nic"
  resource_group_name           = azurerm_resource_group.rg.name
  location                      = azurerm_resource_group.rg.location
  enable_accelerated_networking = true
  tags                          = local.tags

  ip_configuration {
    name                          = "ipconfig1"
    subnet_id                     = azurerm_subnet.default.id
    private_ip_address_allocation = "Dynamic"
    public_ip_address_id          = azurerm_public_ip.pip.id
  }
}

# No template ARM o NSG é associado à NIC (não à subnet) — mantemos a mesma topologia
resource "azurerm_network_interface_security_group_association" "nic_nsg" {
  network_interface_id      = azurerm_network_interface.nic.id
  network_security_group_id = azurerm_network_security_group.nsg.id
}

# ---------------------------------------------------------------------------
# Máquina virtual — Ubuntu 26.04 LTS (ARM64), Standard_D2ps_v6 (série Arm Cobalt)
# Zona de disponibilidade 1, Trusted Launch (Secure Boot + vTPM), Spot instance
# Autenticação somente por chave SSH (disablePasswordAuthentication = true)
# ---------------------------------------------------------------------------
resource "azurerm_linux_virtual_machine" "vm" {
  name                            = "vm-lab-aula01"
  computer_name                   = "vm-lab-aula01"
  resource_group_name             = azurerm_resource_group.rg.name
  location                        = azurerm_resource_group.rg.location
  size                            = var.vm_size
  zone                            = var.zone
  admin_username                  = var.admin_username
  disable_password_authentication = true
  network_interface_ids           = [azurerm_network_interface.nic.id]
  tags                            = local.tags

  # Trusted Launch (igual ao securityProfile do template)
  secure_boot_enabled = true
  vtpm_enabled        = true

  # Spot instance (igual a priority/evictionPolicy/billingProfile do template)
  priority        = "Spot"
  eviction_policy = "Deallocate"
  max_bid_price   = -1

  admin_ssh_key {
    username   = var.admin_username
    public_key = file(pathexpand(var.ssh_public_key_path))
  }

  os_disk {
    caching              = "ReadWrite"
    storage_account_type = "Premium_LRS"
    disk_size_gb         = 30
  }

  disk_controller_type = "SCSI"

  source_image_reference {
    publisher = "canonical"
    offer     = "ubuntu-26_04-lts"
    sku       = "pro-server-arm64"
    version   = "latest"
  }

  boot_diagnostics {} # storage gerenciado pela plataforma (bootDiagnostics enabled)
}
