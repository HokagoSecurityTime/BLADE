FROM python:3.11-slim
ARG BLADE_EXTRAS=""
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /app
COPY pyproject.toml ./
RUN python -c "import os,tomllib; p=tomllib.load(open('pyproject.toml','rb'))['project']; e=os.getenv('BLADE_EXTRAS','').strip('[]').split(','); open('/tmp/requirements.txt','w').write('\n'.join(p['dependencies']+[r for k in e if k for r in p['optional-dependencies'][k]]))" \
    && if echo "$BLADE_EXTRAS" | grep -q rag; then pip install --no-cache-dir torch==2.6.0 --index-url https://download.pytorch.org/whl/cpu; fi \
    && pip install --no-cache-dir -r /tmp/requirements.txt
COPY common ./common
COPY demo_backend ./demo_backend
COPY pipeline ./pipeline
COPY prompts ./prompts
COPY admin_api ./admin_api
COPY proxy ./proxy
COPY scripts ./scripts
RUN pip install --no-cache-dir --no-deps . && mkdir -p /data
WORKDIR /data
