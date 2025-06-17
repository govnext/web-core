# GovNext - Sistema de Gestão Governamental

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/downloads/)
[![Frappe Framework](https://img.shields.io/badge/Frappe-v14-orange)](https://frappeframework.com/)

GovNext é um sistema de gestão governamental moderno baseado no ERPNext, projetado especificamente para atender às necessidades de administrações públicas, com foco inicial em gestão municipal.

## 🎯 Visão Geral

O GovNext moderniza a gestão pública através de uma plataforma integrada que abrange desde o controle orçamentário até o atendimento ao cidadão, proporcionando transparência, eficiência e conformidade com as normas brasileiras.

### ✨ Principais Funcionalidades

#### 🏛️ **Gestão Municipal (Fase Atual)**
- **Tributação Municipal**: IPTU, ISS, taxas e contribuições
- **Licenciamento**: Alvarás, licenças e autorizações
- **Atendimento ao Cidadão**: Portal integrado e ouvidoria
- **Obras e Serviços**: Gestão de infraestrutura municipal
- **Transparência**: Portais de dados abertos e prestação de contas

#### 💰 **Gestão Financeira**
- Orçamento público (LOA, LDO, PPA)
- Execução orçamentária e financeira
- Contabilidade pública (PCASP)
- Tesouraria e fluxo de caixa
- Prestação de contas e relatórios legais

#### 👥 **Recursos Humanos Públicos**
- Folha de pagamento com legislação específica
- Gestão de carreiras e concursos
- Controle de benefícios e vantagens
- Integração com SIAPE e sistemas correlatos

#### 📋 **Licitações e Contratos**
- Processos licitatórios completos
- Gestão de contratos e aditivos
- Cadastro de fornecedores
- Pregão eletrônico

#### 🏢 **Gestão Patrimonial**
- Inventário e controle de bens
- Depreciação conforme normas públicas
- Manutenção preventiva e corretiva
- Baixa e alienação de bens

## 🚀 Instalação

### Pré-requisitos

- Python 3.8+
- Node.js 16+
- MariaDB 10.6+
- Redis 6+
- Git

### Instalação Rápida com Docker

```bash
# Clone o repositório
git clone https://github.com/govnext/govnext.git
cd govnext

# Inicie os serviços
docker-compose up -d

# Acesse: http://localhost:8000
```

### Instalação Manual

```bash
# Instale o Frappe Bench
pip install frappe-bench

# Crie um novo site
bench init govnext-bench
cd govnext-bench

# Crie um site
bench new-site govnext.local --admin-password admin

# Adicione os aplicativos GovNext
bench get-app govnext_core https://github.com/govnext/govnext_core
bench get-app govnext_municipal https://github.com/govnext/govnext_municipal

# Instale os aplicativos
bench --site govnext.local install-app govnext_core
bench --site govnext.local install-app govnext_municipal

# Inicie o servidor
bench start
```

## 📁 Estrutura do Projeto

```
govnext/
├── apps/
│   ├── govnext_core/          # Módulos base e comuns
│   ├── govnext_municipal/     # Específico para municípios
│   ├── govnext_estadual/      # Específico para estados (fase futura)
│   └── govnext_federal/       # Específico para união (fase futura)
├── sites/
│   └── govnext.local/         # Configurações do site
├── config/
│   ├── nginx.conf
│   ├── supervisor.conf
│   └── redis.conf
├── docker/
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── docker-compose.prod.yml
├── docs/                      # Documentação
├── tests/                     # Testes automatizados
└── scripts/                   # Scripts de deploy e manutenção
```

## 🔧 Configuração

### Configuração Básica

1. **Configuração do Site**
```bash
bench --site govnext.local set-config db_name govnext_db
bench --site govnext.local set-config db_password sua_senha_segura
```

2. **Configuração de Email**
```bash
bench --site govnext.local set-config mail_server smtp.gmail.com
bench --site govnext.local set-config mail_port 587
```

3. **Configuração SSL**
```bash
bench setup lets-encrypt govnext.local
```

### Variáveis de Ambiente

```bash
# .env
GOVNEXT_DB_HOST=localhost
GOVNEXT_DB_NAME=govnext_db
GOVNEXT_DB_USER=govnext_user
GOVNEXT_DB_PASSWORD=senha_segura
GOVNEXT_REDIS_URL=redis://localhost:6379
GOVNEXT_SECRET_KEY=chave_secreta_muito_segura
```

## 📚 Documentação

- **[Guia de Instalação](docs/installation.md)**: Instruções detalhadas de instalação
- **[Manual do Usuário](docs/user-guide.md)**: Como usar o sistema
- **[API Reference](docs/api.md)**: Documentação da API REST
- **[Guia do Desenvolvedor](docs/developer-guide.md)**: Como contribuir
- **[Configuração de Módulos](docs/modules.md)**: Configuração específica por módulo

## 🧪 Testes

```bash
# Executar todos os testes
bench --site govnext.local run-tests

# Executar testes específicos
bench --site govnext.local run-tests --module govnext_municipal

# Executar com cobertura
bench --site govnext.local run-tests --coverage
```

## 🚢 Deploy

### Deploy em Produção

```bash
# Clone e configure
git clone https://github.com/govnext/govnext.git
cd govnext

# Configure o ambiente de produção
cp docker-compose.prod.yml docker-compose.yml
docker-compose up -d

# Execute as migrações
docker-compose exec web bench --site govnext.local migrate
```

### Deploy com CI/CD

O projeto inclui configurações para GitHub Actions e GitLab CI:

```yaml
# .github/workflows/deploy.yml
name: Deploy
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Deploy to production
        run: ./scripts/deploy.sh
```

## 🤝 Contribuindo

Contribuições são muito bem-vindas! Por favor, leia nosso [Guia de Contribuição](CONTRIBUTING.md) antes de enviar pull requests.

### Como Contribuir

1. **Fork o projeto**
2. **Crie uma branch para sua feature**
   ```bash
   git checkout -b feature/nova-funcionalidade
   ```

3. **Faça commit das suas alterações**
   ```bash
   git commit -m 'feat: adiciona nova funcionalidade'
   ```

4. **Push para a branch**
   ```bash
   git push origin feature/nova-funcionalidade
   ```

5. **Abra um Pull Request**

### Padrões de Commit

Utilizamos [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` Nova funcionalidade
- `fix:` Correção de bug
- `docs:` Alterações na documentação
- `style:` Formatação de código
- `refactor:` Refatoração de código
- `test:` Adição de testes

## 🛣️ Roadmap

### ✅ Fase 1: Core e Municipal (Atual)
- [x] Configuração base do projeto
- [x] Módulos core do GovNext
- [x] Gestão de IPTU e ISS
- [x] Portal do cidadão básico
- [ ] Sistema de alvarás
- [ ] Gestão de obras municipais

### 🔄 Fase 2: Expansão Municipal (Q3 2025)
- [ ] Ouvidoria integrada
- [ ] Dashboard de gestão
- [ ] Relatórios de transparência
- [ ] App mobile para cidadãos
- [ ] Integração com bancos

### 🔮 Fase 3: Estadual e Federal (2026)
- [ ] Módulos estaduais
- [ ] Módulos federais
- [ ] Integrações avançadas
- [ ] BI e Analytics

## 📄 Licença

Este projeto está licenciado sob a licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

## 📞 Suporte

- **Documentação**: [docs.govnext.org](https://docs.govnext.org)
- **Issues**: [GitHub Issues](https://github.com/govnext/govnext/issues)
- **Discussões**: [GitHub Discussions](https://github.com/govnext/govnext/discussions)
- **Email**: suporte@govnext.org

## 🏆 Reconhecimentos

- [Frappe Framework](https://frappeframework.com/) - Framework base
- [ERPNext](https://erpnext.com/) - Sistema ERP de referência
- Comunidade brasileira de software livre
- Servidores públicos que contribuem com feedback

---
**GovNext** - Modernizando a gestão pública brasileira 🇧🇷
