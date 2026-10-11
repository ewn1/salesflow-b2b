## Preparação do Servidor de Produção

[![CI](https://github.com/ewn1/salesflow-b2b/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/ewn1/salesflow-b2b/actions/workflows/ci.yml)

Antes de subir os containers via Docker Compose em produção, é necessário ajustar a configuração de memória do sistema operacional (Linux) para evitar falhas no Redis:

```bash
# 1. Habilita o overcommit de memória na sessão atual
sudo sysctl vm.overcommit_memory=1

# 2. Torna a mudança permanente mesmo que o servidor seja reiniciado
echo "vm.overcommit_memory = 1" | sudo tee -a /etc/sysctl.conf
