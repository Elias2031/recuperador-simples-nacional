from celery import shared_task
from core.models import UploadLote, Empresa
from core.views.utils.xml_processor import processar_xml
from django.conf import settings
import os, zipfile, tempfile, shutil
from django.contrib.auth import get_user_model


@shared_task
def processar_xml_task(caminho, nome_arquivo, empresa_id, usuario_id):
    print(f"[CELERY] Iniciando processamento do arquivo: {nome_arquivo}")
    resultado = []

    try:
        empresa = Empresa.objects.get(id=empresa_id)
        usuario_model = get_user_model()
        usuario = usuario_model.objects.get(id=usuario_id)

        processar_xml(
            caminho,
            nome_arquivo=nome_arquivo,
            usuario=usuario,
            empresa_ativa=empresa,
            resultado=resultado,
        )

    except Exception as e:
        erro_msg = f"[ERRO CELERY] {e}"
        print(erro_msg)
        resultado.append(erro_msg)

    return resultado
