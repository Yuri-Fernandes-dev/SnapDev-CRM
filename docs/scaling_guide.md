# Guia de Escalabilidade do Sistema CRM

Este documento fornece diretrizes para escalar o sistema CRM à medida que sua base de usuários e dados cresce.

## Estratégias de Escalabilidade

### 1. Escala Vertical (Scaling Up)

Aumento de recursos em um único servidor:

- **Quando usar**: Para crescimento inicial, quando o sistema começa a ficar lento
- **Como implementar**: 
  - Aumento de RAM, CPU e SSD do servidor
  - Otimização do banco de dados PostgreSQL
  - Configuração de caching

**Limites**: Eventualmente, um único servidor terá um teto de capacidade e custos elevados.

### 2. Escala Horizontal (Scaling Out)

Distribuição da carga entre múltiplos servidores:

- **Quando usar**: Quando a escala vertical não é mais suficiente ou custo-efetiva
- **Como implementar**:
  - Configuração de múltiplas instâncias da aplicação
  - Implementação de balanceador de carga (NGINX, HAProxy)
  - Banco de dados com réplicas de leitura
  - Servidores de cache distribuído (Redis)

## Otimizações de Banco de Dados

### Índices

Adicionar índices apropriados para consultas frequentes:

```sql
-- Exemplo: Índice para busca de clientes por nome
CREATE INDEX idx_customer_name ON customers_customer(name);

-- Índice para busca de vendas por data
CREATE INDEX idx_sales_date ON sales_sale(date);

-- Índice composto para relatórios
CREATE INDEX idx_sales_customer_date ON sales_sale(customer_id, date);
```

### Particionamento de Tabelas

Para tabelas que crescem muito (como histórico de vendas):

```sql
-- Exemplo de particionamento por intervalo de data
CREATE TABLE sales_history (
    id SERIAL,
    sale_id INTEGER,
    customer_id INTEGER,
    date DATE,
    amount DECIMAL(10,2)
) PARTITION BY RANGE (date);

-- Criar partições por ano
CREATE TABLE sales_history_2023 PARTITION OF sales_history
    FOR VALUES FROM ('2023-01-01') TO ('2024-01-01');
    
CREATE TABLE sales_history_2024 PARTITION OF sales_history
    FOR VALUES FROM ('2024-01-01') TO ('2025-01-01');
```

### Otimização de Consultas

- Identificar consultas lentas no log do PostgreSQL
- Reescrever ou otimizar consultas problemáticas
- Considerar o uso de procedimentos armazenados para operações complexas

## Implementação de Cache

### Django Cache Framework

Configuração básica no `settings.py`:

```python
# Cache com Redis
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# Cache de sessão
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'
```

### Cache de Views Frequentes

```python
from django.views.decorators.cache import cache_page

# Cache da página por 15 minutos
@cache_page(60 * 15)
def dashboard_view(request):
    # Lógica da view
    return render(request, 'dashboard/index.html', context)
```

### Cache de Consultas Frequentes

```python
from django.core.cache import cache

def get_top_customers():
    # Verificar se resultado está em cache
    cache_key = 'top_customers'
    result = cache.get(cache_key)
    
    if result is None:
        # Consulta cara ao banco de dados
        result = Customer.objects.annotate(
            total_sales=Sum('sale__amount')
        ).order_by('-total_sales')[:10]
        
        # Armazenar em cache por 1 hora
        cache.set(cache_key, result, 60*60)
    
    return result
```

## Processamento Assíncrono

### Celery para Tarefas em Background

Configuração no `settings.py`:

```python
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
```

Implementação em `tasks.py`:

```python
from celery import shared_task
from django.core.mail import send_mail

@shared_task
def process_large_report(report_id):
    # Lógica de processamento demorado
    pass

@shared_task
def send_bulk_emails(customer_ids, subject, message):
    for customer_id in customer_ids:
        customer = Customer.objects.get(id=customer_id)
        send_mail(
            subject,
            message,
            'from@example.com',
            [customer.email],
            fail_silently=False,
        )
```

Uso nas views:

```python
def generate_report(request):
    # Iniciar tarefa assíncrona
    report_id = create_report_record()
    process_large_report.delay(report_id)
    return JsonResponse({'status': 'Report being processed'})
```

## Arquitetura de Microserviços

Para sistemas muito grandes, considere dividir em serviços menores:

1. **Serviço de Clientes**: Gerenciamento de clientes e contatos
2. **Serviço de Vendas**: Processamento e histórico de vendas
3. **Serviço de Relatórios**: Geração de relatórios e análises
4. **Serviço de Notificações**: Emails, SMS e outras comunicações

### Comunicação entre Serviços

- **REST APIs**: Para comunicação síncrona
- **Message Queues** (RabbitMQ, Kafka): Para comunicação assíncrona
- **API Gateway**: Para roteamento unificado

## Monitoramento e Alerta

### Ferramentas Recomendadas

1. **Prometheus**: Coleta de métricas
2. **Grafana**: Visualização de métricas
3. **Sentry**: Rastreamento de erros
4. **New Relic/Datadog**: Monitoramento de performance

### O que Monitorar

- **Tempo de resposta** da aplicação
- **Uso de recursos** (CPU, memória, disco)
- **Estatísticas de banco de dados** (consultas lentas, conexões)
- **Taxa de erros** e exceções
- **Métricas de negócio** (vendas por hora, novos clientes)

## Plano de Escalabilidade por Estágio

### Estágio 1: 1-100 Usuários Concorrentes
- PostgreSQL em servidor único
- Aplicação Django em um ou dois servidores
- Implementar caching básico

### Estágio 2: 100-500 Usuários Concorrentes
- Configurar réplicas de leitura do PostgreSQL
- Implementar balanceamento de carga
- Cache Redis distribuído
- Processamento assíncrono com Celery

### Estágio 3: 500-2000 Usuários Concorrentes
- Particionamento de banco de dados
- Cluster de cache Redis
- Microserviços para componentes críticos
- CDN para conteúdo estático

### Estágio 4: 2000+ Usuários Concorrentes
- Arquitetura completa de microserviços
- Sharding de dados
- Auto-scaling baseado em demanda
- Pipeline de CI/CD robusto

## Considerações de Custo

| Estágio | Infraestrutura | Custo Mensal Estimado |
|---------|----------------|------------------------|
| 1       | 1-2 servidores básicos | R$ 200-500 |
| 2       | 3-5 servidores médios + banco de dados dedicado | R$ 500-1500 |
| 3       | 5-10 servidores + infraestrutura especializada | R$ 1500-5000 |
| 4       | Infraestrutura em nuvem complexa | R$ 5000+ |

## Conclusão

A escalabilidade deve ser planejada com antecedência, mas implementada conforme necessário. Comece com uma base sólida, monitore o crescimento e responda aos gargalos conforme eles surgem, em vez de otimizar prematuramente. 