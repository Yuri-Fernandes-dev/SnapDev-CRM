# Migrando do SQLite para PostgreSQL

Este documento detalha o processo de migração do banco de dados SQLite (usado no ambiente de desenvolvimento) para PostgreSQL (recomendado para produção).

## Por que migrar para PostgreSQL?

O SQLite é excelente para desenvolvimento e pequenas aplicações, mas possui limitações:

1. **Concorrência**: SQLite não lida bem com múltiplos acessos simultâneos
2. **Escalabilidade**: Performance cai com grandes volumes de dados
3. **Funcionalidades**: PostgreSQL oferece recursos avançados como índices, funções, triggers
4. **Segurança**: PostgreSQL possui controle de acesso granular

A migração para PostgreSQL é recomendada quando:
- Seu SaaS atingir 50-100 clientes
- O banco de dados ultrapassar 500MB
- Houver muitos acessos simultâneos (≥ 10 usuários)

## Pré-requisitos

- [PostgreSQL](https://www.postgresql.org/download/) instalado no servidor
- [psycopg2](https://pypi.org/project/psycopg2/) instalado no ambiente Python

## Passo a Passo da Migração

### 1. Instalação das dependências

```bash
pip install psycopg2-binary
```

### 2. Criação do banco de dados PostgreSQL

```sql
CREATE DATABASE saas_crm;
CREATE USER saas_user WITH PASSWORD 'senha_segura';
ALTER ROLE saas_user SET client_encoding TO 'utf8';
ALTER ROLE saas_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE saas_user SET timezone TO 'America/Sao_Paulo';
GRANT ALL PRIVILEGES ON DATABASE saas_crm TO saas_user;
```

### 3. Configuração do Django

Edite o arquivo `saas_crm/settings.py`:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'saas_crm',
        'USER': 'saas_user',
        'PASSWORD': 'senha_segura',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

Para ambientes de produção, é recomendado usar variáveis de ambiente:

```python
import os
import environ

env = environ.Env()
environ.Env.read_env()

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'saas_crm'),
        'USER': os.environ.get('DB_USER', 'saas_user'),
        'PASSWORD': os.environ.get('DB_PASSWORD', 'senha_segura'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}
```

### 4. Exportação dos dados do SQLite

```bash
# Crie um backup completo do banco SQLite
python manage.py dumpdata --exclude auth.permission --exclude contenttypes > db_backup.json

# Opcional: comprima o arquivo para economizar espaço
gzip db_backup.json
```

### 5. Aplicação das migrações no PostgreSQL

```bash
# Certifique-se de que o settings.py já está configurado para PostgreSQL
python manage.py migrate

# Carregue os dados do backup
python manage.py loaddata db_backup.json
```

### 6. Verificação da migração

```bash
# Verifique se os dados foram migrados corretamente
python manage.py shell

# No shell:
from products.models import Product
Product.objects.count()  # Deve retornar o mesmo número que no SQLite

from customers.models import Customer
Customer.objects.count()  # Deve retornar o mesmo número que no SQLite

from sales.models import Sale
Sale.objects.count()  # Deve retornar o mesmo número que no SQLite
```

### 7. Ajustes pós-migração

Após confirmar que a migração foi bem-sucedida:

1. **Otimização do PostgreSQL**:
```sql
-- Analise as tabelas para otimização
ANALYZE;

-- Crie índices para campos frequentemente consultados
CREATE INDEX idx_product_name ON products_product(name);
CREATE INDEX idx_customer_name ON customers_customer(name);
CREATE INDEX idx_sale_created ON sales_sale(created_at);
```

2. **Backup automático**:
Configure backups automáticos utilizando uma ferramenta como o [pg_dump](https://www.postgresql.org/docs/current/app-pgdump.html):

```bash
# Exemplo de script de backup
pg_dump -U saas_user -d saas_crm -F c -f /path/to/backups/saas_crm_$(date +%Y%m%d).dump
```

## Considerações para alta disponibilidade

Para aplicações em escala ainda maior (mais de 500 clientes ativos), considere:

1. **Read Replicas**: Configure réplicas de leitura para distribuir a carga
2. **Connection Pooling**: Utilize PgBouncer para gerenciar conexões
3. **Sharding**: Para volumes muito grandes, considere particionar os dados
4. **Monitoramento**: Configure ferramentas como Prometheus e Grafana

## Solução de problemas comuns

1. **Erro de codificação**:
   - Certifique-se de que todos os bancos usam a mesma codificação (UTF-8)

2. **Tipos de dados incompatíveis**:
   - SQLite é menos rigoroso com tipos. Corrija os dados antes da migração.

3. **Problemas de permissão**:
   - Verifique se o usuário do PostgreSQL tem as permissões necessárias.

4. **Timeout durante a carga**:
   - Para bancos grandes, aumente os timeouts no PostgreSQL e no Django.

## Referências

- [Documentação do Django sobre bancos de dados](https://docs.djangoproject.com/en/4.2/ref/databases/)
- [Documentação do PostgreSQL](https://www.postgresql.org/docs/)
- [Tutorial de migração SQLite para PostgreSQL](https://www.digitalocean.com/community/tutorials/sqlite-vs-mysql-vs-postgresql-a-comparison-of-relational-database-management-systems) 