FROM python:3.12-slim

# Instala o uv para gerenciamento de dependências
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Copia os arquivos de configuração do uv (se existirem) e o código
COPY pyproject.toml uv.lock* ./
COPY . .

# Instala as dependências (se houver) e prepara o ambiente virtual
# O --frozen garante que o lockfile não seja alterado no container
RUN uv sync --frozen

# Define o PYTHONPATH para garantir que o diretório 'src' seja reconhecido
ENV PYTHONPATH=/app

# Expõe a porta padrão
EXPOSE 5000

# Comando padrão: inicia o nó ouvindo em todas as interfaces
CMD ["uv", "run", "python", "main.py", "--host", "0.0.0.0", "--port", "5000"]
