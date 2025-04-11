# Estratégias de Backup e Recuperação

Este documento descreve práticas recomendadas para backup e recuperação de dados do sistema CRM Django.

## Tipos de Backup

### 1. Backup do Banco de Dados

#### Para PostgreSQL

**Backup Completo**

```bash
# Backup em formato SQL (texto)
pg_dump -U usuario -d nome_do_banco -f backup_completo.sql

# Backup compactado
pg_dump -U usuario -d nome_do_banco | gzip > backup_completo.sql.gz

# Backup em formato binário (mais eficiente para restauração)
pg_dump -U usuario -d nome_do_banco -Fc -f backup_completo.dump
```

**Backup Incremental**

Para PostgreSQL, use WAL (Write-Ahead Logging):

```bash
# No postgresql.conf
wal_level = replica
archive_mode = on
archive_command = 'cp %p /caminho/para/arquivos/wal/%f'
```

#### Para SQLite (Desenvolvimento)

```bash
# Simples cópia do arquivo
cp db.sqlite3 backup_$(date +%Y%m%d).sqlite3

# Com compressão
sqlite3 db.sqlite3 .dump | gzip > backup_$(date +%Y%m%d).sql.gz
```

### 2. Backup de Arquivos de Mídia

```bash
# Sincronizar diretório de mídia com destino de backup
rsync -avz --delete /caminho/para/media/ /caminho/para/backup/media/

# Compactar diretório de mídia
tar -czvf media_backup_$(date +%Y%m%d).tar.gz /caminho/para/media/
```

### 3. Backup de Código e Configurações

```bash
# Usando Git
git archive --format=zip --output=codigo_$(date +%Y%m%d).zip HEAD

# Backup manual de arquivos de configuração
cp .env .env.backup_$(date +%Y%m%d)
cp saas_crm/settings.py saas_crm/settings.py.backup_$(date +%Y%m%d)
```

## Estratégias de Programação de Backup

### Backups Automáticos Diários

**Usando Cron (Linux/Unix)**

```bash
# Editar crontab
crontab -e

# Adicionar linha para backup diário às 02:00
0 2 * * * /caminho/para/script_de_backup.sh
```

**Script de Backup Completo (script_de_backup.sh)**

```bash
#!/bin/bash

# Variáveis
DATE=$(date +%Y%m%d)
BACKUP_DIR="/caminho/para/backups"
DB_USER="usuario_db"
DB_NAME="nome_do_banco"
APP_DIR="/caminho/para/aplicacao"
MEDIA_DIR="/caminho/para/media"

# Criar diretório de backup datado
mkdir -p $BACKUP_DIR/$DATE

# Backup do banco de dados
pg_dump -U $DB_USER -d $DB_NAME -Fc -f $BACKUP_DIR/$DATE/database.dump

# Backup de mídias
tar -czvf $BACKUP_DIR/$DATE/media.tar.gz $MEDIA_DIR

# Backup de configurações
cp $APP_DIR/.env $BACKUP_DIR/$DATE/
cp $APP_DIR/saas_crm/settings.py $BACKUP_DIR/$DATE/

# Remover backups mais antigos que 30 dias
find $BACKUP_DIR/* -type d -mtime +30 -exec rm -rf {} \;

# Registrar conclusão
echo "Backup completo concluído em $(date)" >> $BACKUP_DIR/backup_log.txt
```

### Usando o TaskScheduler no Windows

Para ambientes Windows, crie um arquivo `.bat`:

```batch
@echo off
set DATE=%date:~6,4%%date:~3,2%%date:~0,2%
set BACKUP_DIR=C:\backups

REM Criar diretório de backup
mkdir %BACKUP_DIR%\%DATE%

REM Backup do banco de dados
"C:\Program Files\PostgreSQL\14\bin\pg_dump.exe" -U postgres -d nome_do_banco -Fc -f %BACKUP_DIR%\%DATE%\database.dump

REM Backup de mídias
"C:\Program Files\7-Zip\7z.exe" a %BACKUP_DIR%\%DATE%\media.zip C:\caminho\para\media\

REM Backup de configurações
copy C:\caminho\para\aplicacao\.env %BACKUP_DIR%\%DATE%\
copy C:\caminho\para\aplicacao\saas_crm\settings.py %BACKUP_DIR%\%DATE%\

echo Backup completo em %DATE% >> %BACKUP_DIR%\backup_log.txt
```

## Estratégias de Armazenamento

### Regra 3-2-1 para Backups Críticos

1. Mantenha pelo menos **3 cópias** dos dados
2. Armazene em **2 tipos diferentes** de mídia
3. Mantenha **1 cópia off-site** (em local físico diferente)

### Rotação de Backups

- **Diários**: Manter por 7-14 dias
- **Semanais**: Manter por 4-8 semanas
- **Mensais**: Manter por 12 meses
- **Anuais**: Manter indefinidamente (arquivamento)

### Armazenamento em Nuvem

Configure o upload automático dos backups para serviços como:

- Amazon S3
- Google Cloud Storage
- Microsoft Azure Blob Storage
- Backblaze B2

**Exemplo de script para upload no Amazon S3**:

```bash
#!/bin/bash
DATE=$(date +%Y%m%d)
BACKUP_DIR="/caminho/para/backups/$DATE"

# Upload para S3
aws s3 sync $BACKUP_DIR s3://nome-do-bucket/backups/$DATE/

# Verificar sucesso
if [ $? -eq 0 ]; then
    echo "Upload para S3 concluído com sucesso" >> /caminho/para/backups/backup_log.txt
else
    echo "ERRO: Upload para S3 falhou" >> /caminho/para/backups/backup_log.txt
fi
```

## Procedimentos de Recuperação

### Restauração do Banco de Dados PostgreSQL

```bash
# Restaurar de um arquivo SQL
psql -U usuario -d nome_do_banco -f backup_completo.sql

# Restaurar de um arquivo binário (.dump)
pg_restore -U usuario -d nome_do_banco -c backup_completo.dump
```

### Restauração do Banco de Dados SQLite

```bash
# Restaurar de uma cópia
cp backup_20240101.sqlite3 db.sqlite3

# Restaurar de um dump SQL
sqlite3 db.sqlite3 < backup_20240101.sql
```

### Restauração de Arquivos de Mídia

```bash
# Descompactar arquivos
tar -xzvf media_backup_20240101.tar.gz -C /caminho/para/restauracao/

# Sincronizar diretórios
rsync -avz /caminho/para/backup/media/ /caminho/para/media/
```

## Testes de Recuperação

### Procedimento de Teste Mensal

1. Criar um ambiente de teste isolado
2. Restaurar o banco de dados mais recente no ambiente de teste
3. Restaurar arquivos de mídia
4. Verificar a integridade dos dados restaurados
5. Documentar o resultado do teste

**Exemplo de Teste**:

```bash
#!/bin/bash
# Script para testar a recuperação de backup

# Configuração
TEST_DIR="/caminho/para/teste_recuperacao"
LATEST_BACKUP=$(ls -t /caminho/para/backups/ | head -1)
BACKUP_DIR="/caminho/para/backups/$LATEST_BACKUP"

# Preparar ambiente de teste
mkdir -p $TEST_DIR
mkdir -p $TEST_DIR/media

# Restaurar banco de dados em um banco de teste
createdb teste_recuperacao
pg_restore -U usuario -d teste_recuperacao $BACKUP_DIR/database.dump

# Restaurar arquivos de mídia
tar -xzvf $BACKUP_DIR/media.tar.gz -C $TEST_DIR/media/

# Executar testes de verificação
echo "Iniciando verificação de dados em $(date)" > $TEST_DIR/resultado_teste.txt
echo "Contagem de usuários: $(psql -U usuario -d teste_recuperacao -c "SELECT COUNT(*) FROM auth_user" -t)" >> $TEST_DIR/resultado_teste.txt
echo "Contagem de clientes: $(psql -U usuario -d teste_recuperacao -c "SELECT COUNT(*) FROM customers_customer" -t)" >> $TEST_DIR/resultado_teste.txt
echo "Contagem de vendas: $(psql -U usuario -d teste_recuperacao -c "SELECT COUNT(*) FROM sales_sale" -t)" >> $TEST_DIR/resultado_teste.txt

# Verificar arquivos de mídia
echo "Arquivos de mídia encontrados: $(find $TEST_DIR/media -type f | wc -l)" >> $TEST_DIR/resultado_teste.txt

# Limpar após o teste
dropdb teste_recuperacao
echo "Teste de recuperação concluído em $(date)" >> $TEST_DIR/resultado_teste.txt
```

## Plano de Recuperação de Desastres (PRD)

### Níveis de Desastre

1. **Nível 1**: Corrupção de dados ou exclusão acidental
2. **Nível 2**: Falha de hardware local
3. **Nível 3**: Desastre no data center/local principal
4. **Nível 4**: Desastre regional/catástrofe

### Procedimentos por Nível

#### Nível 1: Corrupção de Dados

1. Suspender o acesso dos usuários ao sistema
2. Identificar a extensão da corrupção/perda
3. Restaurar apenas os dados afetados do backup mais recente
4. Verificar integridade
5. Restaurar o acesso dos usuários

#### Nível 2: Falha de Hardware

1. Ativar servidor/infraestrutura de backup (se disponível)
2. Restaurar banco de dados e arquivos no novo hardware
3. Atualizar configurações DNS se necessário
4. Verificar funcionalidade completa antes de reestabelecer acesso

#### Nível 3-4: Desastre Maior

1. Ativar site de recuperação em região diferente
2. Restaurar a partir dos backups off-site mais recentes
3. Informar os usuários sobre possível perda de dados recentes
4. Reconfigurar DNS para apontar para o novo site
5. Implementar plano de retorno quando o site principal for restaurado

### Papéis e Responsabilidades

| Papel | Responsabilidade | Contato |
|-------|------------------|---------|
| Administrador do Banco de Dados | Restauração de dados | [email/telefone] |
| Administrador de Sistemas | Restauração de servidores e infraestrutura | [email/telefone] |
| Coordenador de TI | Coordenar esforços de recuperação | [email/telefone] |
| Líder do Projeto | Comunicação com stakeholders | [email/telefone] |

## Documentação e Treinamento

1. Manter este documento atualizado após mudanças significativas
2. Realizar treinamento anual com equipe de TI sobre procedimentos de backup/restauração
3. Revisar e atualizar o plano de recuperação de desastres semestralmente
4. Documentar cada incidente de recuperação e lições aprendidas

## Conclusão

Um sistema robusto de backup e recuperação é essencial para a continuidade dos negócios. Este documento deve ser tratado como um guia vivo, sendo constantemente atualizado conforme o sistema evolui e novas ameaças são identificadas. 