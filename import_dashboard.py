import urllib.request
import urllib.error
import json
import base64
import re
import sys

GRAFANA_URL = "http://localhost:3001"
AUTH_HEADER = "Basic " + base64.b64encode(b"admin:admin").decode("utf-8")

def make_request(path, data=None, method=None):
    url = f"{GRAFANA_URL}{path}"
    headers = {
        "Authorization": AUTH_HEADER,
        "Content-Type": "application/json"
    }
    
    req_data = json.dumps(data).encode("utf-8") if data is not None else None
    
    if method is None:
        method = "POST" if data is not None else "GET"
        
    req = urllib.request.Request(url, data=req_data, headers=headers, method=method)
    
    try:
        with urllib.request.urlopen(req) as res:
            return json.loads(res.read().decode("utf-8")), res.status
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        # Se for 409 (already exists) no POST datasources ou 404 no GET, não exibimos traceback
        if not (path == "/api/datasources" and e.code == 409) and not (path.startswith("/api/datasources/name") and e.code == 404):
            print(f"[DEBUG API Error] Path: {path} | Status: {e.code} | Resposta: {err_body}")
        try:
            return json.loads(err_body), e.code
        except:
            return {"error": err_body}, e.code
    except Exception as e:
        print(f"[DEBUG Exception] {e}")
        return None, None

def main():
    print("Iniciando importação automática do Dashboard para o Grafana...")
    
    # 1. Tenta buscar fonte de dados existente pelo nome
    ds_check, check_status = make_request("/api/datasources/name/Prometheus", method="GET")
    
    datasource_payload = {
        "name": "Prometheus",
        "type": "prometheus",
        "url": "http://rpg-prometheus:9090",
        "access": "proxy",
        "isDefault": True
    }
    
    if check_status == 200 and ds_check and "id" in ds_check:
        ds_id = ds_check["id"]
        # Atualiza existente usando PUT para forçar a URL correta (corrige 'empty url' 500)
        print(f"Fonte de dados 'Prometheus' existente encontrada (ID {ds_id}). Atualizando URL para http://rpg-prometheus:9090...")
        res, status = make_request(f"/api/datasources/{ds_id}", datasource_payload, method="PUT")
        if status == 200:
            print("Fonte de dados Prometheus atualizada com sucesso no Grafana.")
        else:
            print(f"Erro ao atualizar fonte de dados Prometheus (Status {status}): {res}")
    else:
        # Tenta criar nova usando POST
        print("Criando nova fonte de dados 'Prometheus' no Grafana...")
        res, status = make_request("/api/datasources", datasource_payload, method="POST")
        if status == 200:
            print("Fonte de dados Prometheus created com sucesso no Grafana.")
        else:
            print(f"Erro ao criar fonte de dados Prometheus (Status {status}): {res}")

    # 2. Extrai o JSON do dashboard do arquivo md
    try:
        with open("/var/www/rpg/docs/telemetry_dashboard.md", "r", encoding="utf-8") as f:
            content = f.read()
        
        # Encontra o bloco json
        match = re.search(r"```json\s*(.*?)\s*```", content, re.DOTALL)
        if not match:
            print("Erro: JSON do dashboard não encontrado em telemetry_dashboard.md.")
            sys.exit(1)
            
        dashboard_json = json.loads(match.group(1))
        # Define id como None para forçar a criação de um novo dashboard
        dashboard_json["id"] = None
    except Exception as e:
        print(f"Erro ao ler ou processar telemetry_dashboard.md: {e}")
        sys.exit(1)

    # 3. Importa o dashboard
    dashboard_payload = {
        "dashboard": dashboard_json,
        "overwrite": True
    }
    
    res, status = make_request("/api/dashboards/db", dashboard_payload)
    if res and status == 200:
        print("\n[SUCESSO] Dashboard do RPG de texto importado com êxito!")
        print(f"➔ Acesse em seu navegador: http://localhost:3001/d/{res.get('uid')}")
    else:
        print(f"\n[ERRO] Falha ao importar o Dashboard. Retorno da API: {res}")
        sys.exit(1)

if __name__ == "__main__":
    main()
