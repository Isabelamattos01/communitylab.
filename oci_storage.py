import os
import json
import logging
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("CommunityLab.OCI")

def salvar_ativo_no_oci(dados_ativo: Dict[str, Any], nome_objeto: str) -> Dict[str, Any]:
    """
    Persiste o pacote de ativos gerado no OCI Object Storage (Always Free).
    Garante fallback automático para ambiente local de desenvolvimento.
    """
    modo_simulado = os.getenv("MODO_SIMULACAO_OCI", "false").lower() == "true"
    bucket_name = os.getenv("OCI_BUCKET_NAME", "communitylab-ativos-marketing")
    
    if modo_simulado:
        os.makedirs("oci_local_storage", exist_ok=True)
        caminho_local = os.path.join("oci_local_storage", nome_objeto.replace("/", "_"))
        with open(caminho_local, "w", encoding="utf-8") as f:
            json.dump(dados_ativo, f, ensure_ascii=False, indent=2)
        return {
            "bucket": bucket_name,
            "caminho_objeto": f"simulado/{nome_objeto}",
            "status": "salvo_com_sucesso (modo_local_homologado)",
            "storage_tier": "Standard (Always Free Simulated)"
        }

    try:
        import oci
        config_path = os.path.expanduser(os.getenv("OCI_CONFIG_FILE", "~/.oci/config"))
        profile = os.getenv("OCI_CONFIG_PROFILE", "DEFAULT")
        config = oci.config.from_file(config_path, profile)
        
        object_storage_client = oci.object_storage.ObjectStorageClient(config)
        namespace = os.getenv("OCI_NAMESPACE") or object_storage_client.get_namespace().data
        
        payload_bytes = json.dumps(dados_ativo, ensure_ascii=False, indent=2).encode("utf-8")

        object_storage_client.put_object(
            namespace_name=namespace,
            bucket_name=bucket_name,
            object_name=nome_objeto,
            put_object_body=payload_bytes,
            content_type="application/json"
        )
        return {
            "bucket": bucket_name,
            "caminho_objeto": nome_objeto,
            "status": "salvo_com_sucesso",
            "storage_tier": "Standard (Always Free)"
        }
    except Exception as e:
        logger.error(f"Erro ao persistir no OCI Object Storage: {str(e)}")
        return {
            "bucket": bucket_name,
            "caminho_objeto": nome_objeto,
            "status": f"erro_oci: {str(e)}",
            "storage_tier": "N/A"
        }
