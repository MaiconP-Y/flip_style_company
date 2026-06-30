# Flip Style Company - Catálogo Digital (Vitrine)

## Visão Geral do Projeto
Este projeto é a plataforma digital oficial da **Flip Style Company**. Atualmente, o sistema opera como um catálogo vitrine de produtos de alta performance. Foi arquitetado visando escalabilidade total: sua base de dados e estrutura de aplicações estão escaláveis para, no futuro, receber módulos de carrinho, checkout e pagamentos sem a necessidade de reescrever o sistema.

Nesta fase, o site foca em navegação rápida, SEO otimizado e conversão direta via WhatsApp, não coletando dados sensíveis.

## Stack Tecnológico e Arquitetura
A plataforma foi construída com tecnologias modernas, focadas em estabilidade e fácil manutenção:

*   **Backend:** Python 3.12 com Django 5.2.
*   **Banco de Dados:** PostgreSQL 17, garantindo integridade e capacidade robusta para o futuro e-commerce.
*   **Servidor de Aplicação:** Gunicorn configurado para alta concorrência.
*   **Arquivos Estáticos:** Gerenciados de forma nativa e otimizada via Whitenoise.
*   **Infraestrutura:** Totalmente containerizado usando Docker e Docker Compose, dividindo a aplicação em serviços independentes de banco de dados (`db`) e aplicação web (`web`).

## Como Rodar o Projeto (Ambiente Local)

Graças à infraestrutura em Docker, rodar o projeto em qualquer máquina requer apenas alguns comandos.

### 1. Pré-requisitos
Certifique-se de ter instalado em sua máquina:
*   [Docker]
*   [Docker Compose]

### 2. Configuração de Variáveis de Ambiente
Na raiz do projeto, crie um arquivo chamado `.env` e preencha com as credenciais do banco de dados e da aplicação. *(Confira o arquivo `.env.example` para ver as chaves necessárias).*

### 3. Iniciando os Containers
No terminal, execute o comando abaixo para construir as imagens e subir os containers:
```bash
docker-compose up --build