# Guia de Segurança para CRM Django

## Índice
1. [Autenticação e Autorização](#autenticação-e-autorização)
2. [Proteção de Dados](#proteção-de-dados)
3. [Segurança de API](#segurança-de-api)
4. [Segurança de Infraestrutura](#segurança-de-infraestrutura)
5. [Conformidade com Regulamentos](#conformidade-com-regulamentos)
6. [Monitoramento e Resposta a Incidentes](#monitoramento-e-resposta-a-incidentes)
7. [Checklist de Segurança](#checklist-de-segurança)

## Autenticação e Autorização

### Implementação de Autenticação Forte
- Utilize o sistema de autenticação do Django com senhas fortes
- Implemente autenticação de dois fatores (2FA)
- Configure bloqueio de conta após várias tentativas falhas de login

```python
# Configuração para bloqueio de conta após tentativas falhas (settings.py)
AXES_FAILURE_LIMIT = 5
AXES_COOLOFF_TIME = 1  # Em horas
AXES_LOCK_OUT_AT_FAILURE = True
INSTALLED_APPS += ['axes']
MIDDLEWARE += ['axes.middleware.AxesMiddleware']
AUTHENTICATION_BACKENDS = [
    'axes.backends.AxesBackend',
    'django.contrib.auth.backends.ModelBackend',
]
```

### Permissões e Controle de Acesso
- Implemente permissões granulares baseadas em papéis
- Utilize grupos do Django para gerenciar permissões
- Restrinja acesso a views usando decoradores
  
```python
from django.contrib.auth.decorators import permission_required

@permission_required('core.view_company')
def company_details(request, company_id):
    # Lógica de visualização
    pass
```

## Proteção de Dados

### Criptografia
- Utilize HTTPS em todos os ambientes (incluindo desenvolvimento)
- Criptografe dados sensíveis no banco de dados
- Use bibliotecas como `django-cryptography` para campos sensíveis

```python
from django_cryptography.fields import encrypt

class Company(models.Model):
    # Campos básicos...
    cnpj = encrypt(models.CharField(max_length=14))
    # Outros campos...
```

### Sanitização de Entrada e Validação
- Valide todas as entradas do usuário
- Utilize formulários do Django para validação automática
- Implemente validação específica para dados críticos como CNPJ

```python
from django import forms
import re

class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = ['name', 'cnpj', 'email', 'phone']
    
    def clean_cnpj(self):
        cnpj = self.cleaned_data['cnpj']
        if not re.match(r'^\d{14}$', cnpj):
            raise forms.ValidationError('CNPJ deve conter 14 dígitos numéricos')
        # Mais validações...
        return cnpj
```

## Segurança de API

### Autenticação e Autorização API
- Utilize tokens de autenticação para APIs
- Implemente OAuth2 para integrações com terceiros
- Utilize Django REST Framework com permissões adequadas

```python
# settings.py
INSTALLED_APPS += ['rest_framework', 'oauth2_provider']
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'oauth2_provider.contrib.rest_framework.OAuth2Authentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ]
}
```

### Proteção contra Ataques Comuns
- Implemente rate limiting para evitar ataques de força bruta
- Proteja contra CSRF, XSS e SQL Injection
- Utilize CORS corretamente para APIs

```python
# settings.py
MIDDLEWARE += ['django.middleware.csrf.CsrfViewMiddleware']
CORS_ALLOWED_ORIGINS = [
    "https://cliente1.example.com",
    "https://cliente2.example.com",
]
```

## Segurança de Infraestrutura

### Configuração de Servidor
- Mantenha o Django e todas as dependências atualizadas
- Desative o modo DEBUG em produção
- Configure cabeçalhos de segurança HTTP
- Utilize servidores web como Nginx ou Apache como proxy reverso

```python
# settings.py para produção
DEBUG = False
ALLOWED_HOSTS = ['crm.example.com']
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000  # 1 ano
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
```

### Backup e Recuperação
- Implemente backups automáticos e regulares
- Teste os procedimentos de recuperação periodicamente
- Criptografe os backups

## Conformidade com Regulamentos

### LGPD (Lei Geral de Proteção de Dados)
- Documente todos os dados pessoais armazenados
- Implemente funcionalidades para exclusão de dados e portabilidade
- Obtenha consentimento explícito para processamento de dados

### PCI DSS (Se Aplicável)
- Não armazene dados de cartão de crédito completos
- Utilize serviços de pagamento certificados
- Realize varreduras regulares de segurança

## Monitoramento e Resposta a Incidentes

### Logging
- Configure logging detalhado para ações críticas
- Utilize o Django Logging para capturar erros
- Armazene logs em locais seguros e centralizados

```python
# settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'WARNING',
            'class': 'logging.FileHandler',
            'filename': '/var/log/django/crm_security.log',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django.security': {
            'handlers': ['file'],
            'level': 'WARNING',
            'propagate': True,
        },
    },
}
```

### Plano de Resposta a Incidentes
- Desenvolva um plano detalhado para resposta a incidentes
- Designe responsáveis para coordenação de resposta
- Documente procedimentos para comunicação e mitigação

## Checklist de Segurança

### Pré-Implantação
- [ ] Revisão de código para vulnerabilidades de segurança
- [ ] Teste de penetração (pentest)
- [ ] Configuração de firewall e WAF
- [ ] Verificação de todas as dependências por vulnerabilidades conhecidas

### Manutenção Contínua
- [ ] Monitoramento de tráfego anormal
- [ ] Atualizações regulares de dependências
- [ ] Auditorias de segurança trimestrais
- [ ] Treinamento da equipe em práticas de segurança
- [ ] Revisão e atualização das políticas de segurança

### Ferramentas Recomendadas
- **Bandit**: Análise estática de código Python
- **OWASP ZAP**: Teste de segurança de aplicações web
- **Django Security Check**: Verificação de configurações de segurança do Django
- **Sentry**: Monitoramento de erros e problemas de segurança em tempo real 