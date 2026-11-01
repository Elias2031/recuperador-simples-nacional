# core/views/upload.py

import os
import zipfile
import tempfile
import shutil
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.core.files.storage import FileSystemStorage
from django.conf import settings
from core.models import Empresa, NotaFiscal, UploadLote
from core.views.utils.xml_processor import processar_xml
from django.contrib import messages
from core.services.extracao import extrair_dados_pgdas
from core.models import Empresa, Competencia, PgdasValorDeclarado, ApuracaoFiscal, ArquivoImportado
from core.tasks import processar_xml_task


def limpar_valor(valor):
    """
    Garante que o valor seja tratado como número decimal.
    Se for string com vírgula, converte. Se já for float ou int, retorna como está.
    """
    if isinstance(valor, (int, float)):
        return float(valor)
    if not valor:
        return 0.0
    return float(str(valor).replace('.', '').replace(',', '.'))

@login_required
def upload_view(request):
    if not request.session.get('empresa_id'):
        messages.error(request, "❌ Selecione uma empresa antes de importar arquivos.")
        return redirect('empresas_view')

    try:
        empresa_ativa = Empresa.objects.get(id=request.session['empresa_id'], usuario=request.user)
    except Empresa.DoesNotExist:
        messages.error(request, "❌ Empresa selecionada inválida.")
        return redirect('empresas_view')

    resultado = []
    uploads = UploadLote.objects.filter(empresa=empresa_ativa).order_by('-data_envio')[:20]

    if request.method == 'POST' and request.FILES.getlist('arquivos'):
        arquivos = request.FILES.getlist('arquivos')
        fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'uploads'))

        upload_lote = UploadLote.objects.create(
            empresa=empresa_ativa,
            usuario=request.user,
            status='AGUARDANDO',
            observacao=f"{len(arquivos)} arquivos recebidos."
        )

        for arquivo in arquivos:
            nome = fs.save(arquivo.name, arquivo)
            caminho = fs.path(nome)
            extensao = os.path.splitext(nome)[-1].lower()

            try:
                if extensao == '.zip':
                    with zipfile.ZipFile(caminho, 'r') as zip_ref:
                        with tempfile.TemporaryDirectory() as tmp_dir:
                            zip_ref.extractall(tmp_dir)
                            for item in zip_ref.namelist():
                                if item.lower().endswith('.xml'):
                                    origem = os.path.join(tmp_dir, item)
                                    destino = _salvar_arquivo_xml_local(item, origem)

                                    processar_xml_task.delay(
                                        caminho=destino,
                                        nome_arquivo=item,
                                        empresa_id=empresa_ativa.id,
                                        usuario_id=request.user.id
                                    )

                                    ArquivoImportado.objects.create(
                                        upload_lote=upload_lote,
                                        nome_arquivo=item,
                                        tipo='XML',
                                        status='OK',
                                        mensagem='XML dentro de ZIP agendado com sucesso.'
                                    )
                    messages.success(request, f"📦 ZIP '{arquivo.name}' agendado.")

                elif extensao == '.xml':
                    destino = _salvar_arquivo_xml_local(nome, caminho)

                    processar_xml_task.delay(
                        caminho=destino,
                        nome_arquivo=nome,
                        empresa_id=empresa_ativa.id,
                        usuario_id=request.user.id
                    )

                    ArquivoImportado.objects.create(
                        upload_lote=upload_lote,
                        nome_arquivo=nome,
                        tipo='XML',
                        status='OK',
                        mensagem='XML agendado com sucesso.'
                    )

                    messages.success(request, f"🧾 XML '{arquivo.name}' agendado para processamento.")

                elif extensao == '.pdf':
                    destino = _salvar_arquivo_pgdas_local(nome, caminho)
                    dados_pgdas = extrair_dados_pgdas(caminho)
                    total_pgdas = 0

                    for cnpj_completo, dados in dados_pgdas.items():
                        try:
                            cnpj_base = cnpj_completo.zfill(14)[:8]
                            empresa = Empresa.objects.filter(cnpj__startswith=cnpj_base).first()
                            if not empresa:
                                continue

                            mes, ano = map(int, dados['periodo'].split('_'))
                            competencia, _ = Competencia.objects.get_or_create(mes=mes, ano=ano)

                            pgdas, _ = PgdasValorDeclarado.objects.update_or_create(
                                empresa=empresa,
                                competencia=competencia,
                                defaults={
                                    'arquivo_pdf': f'pgdas/{os.path.basename(destino)}',
                                    'receita_bruta': limpar_valor(dados['receita_bruta']),
                                    'valor_rbt12': limpar_valor(dados['valor_rbt12']),
                                    'valor_IRPJ_pago_original': limpar_valor(dados['valor_IRPJ_pago_original']),
                                    'valor_CSLL_pago_original': limpar_valor(dados['valor_CSLL_pago_original']),
                                    'valor_COFINS_pago_original': limpar_valor(dados['valor_COFINS_pago_original']),
                                    'valor_PIS_pago_original': limpar_valor(dados['valor_PIS_pago_original']),
                                    'valor_INSS_pago_original': limpar_valor(dados['valor_INSS_pago_original']),
                                    'valor_ICMS_pago_original': limpar_valor(dados['valor_ICMS_pago_original']),
                                    'valor_IPI_pago_original': limpar_valor(dados['valor_IPI_pago_original']),
                                    'valor_ISS_pago_original': limpar_valor(dados['valor_ISS_pago_original']),
                                    'valor_DAS_pago_original': limpar_valor(dados['valor_DAS_pago_original']),
                                }
                            )

                            apuracao = ApuracaoFiscal.objects.filter(
                                empresa=empresa,
                                competencia=competencia
                            ).first()
                            if apuracao:
                                apuracao.pgdas = pgdas
                                apuracao.save()

                            total_pgdas += 1

                        except Exception as e:
                            ArquivoImportado.objects.create(
                                upload_lote=upload_lote,
                                nome_arquivo=nome,
                                tipo='PDF',
                                status='ERRO',
                                mensagem=f"Erro para CNPJ {cnpj_completo}: {e}"
                            )

                    if total_pgdas > 0:
                        ArquivoImportado.objects.create(
                            upload_lote=upload_lote,
                            nome_arquivo=nome,
                            tipo='PDF',
                            status='OK',
                            mensagem=f"{total_pgdas} declarações PGDAS importadas."
                        )
                        messages.success(request, f"📄 {total_pgdas} PGDAS importadas.")
                    else:
                        ArquivoImportado.objects.create(
                            upload_lote=upload_lote,
                            nome_arquivo=nome,
                            tipo='PDF',
                            status='IGNORADO',
                            mensagem='Nenhum PGDAS válido encontrado.'
                        )
                        messages.warning(request, f"⚠️ Nenhum PGDAS válido no PDF '{arquivo.name}'.")

                else:
                    ArquivoImportado.objects.create(
                        upload_lote=upload_lote,
                        nome_arquivo=arquivo.name,
                        tipo=extensao.upper(),
                        status='IGNORADO',
                        mensagem='Extensão não suportada.'
                    )
                    messages.warning(request, f"⚠️ Arquivo '{arquivo.name}' ignorado.")

            except Exception as e:
                ArquivoImportado.objects.create(
                    upload_lote=upload_lote,
                    nome_arquivo=arquivo.name,
                    tipo=extensao.upper(),
                    status='ERRO',
                    mensagem=f"Erro ao processar: {e}"
                )
                messages.error(request, f"❌ Erro ao processar '{arquivo.name}': {e}")

        qtd_ok = upload_lote.arquivos.filter(status='OK').count()
        qtd_erro = upload_lote.arquivos.filter(status='ERRO').count()

        if qtd_ok > 0 and qtd_erro == 0:
            upload_lote.status = 'CONCLUIDO'
        elif qtd_ok == 0 and qtd_erro > 0:
            upload_lote.status = 'ERRO'
        else:
            upload_lote.status = 'CONCLUIDO'  # ou 'PARCIAL'

        upload_lote.save()

    else:
        messages.info(request, "ℹ️ Nenhum arquivo foi enviado.")

    return render(request, 'upload.html', {
        'resultado': resultado,
        'uploads': uploads,
        'arquivos_por_lote': {
        upload.id: upload.arquivos.all()
        for upload in uploads
        }
    })

def _salvar_arquivo_xml_local(nome_arquivo, origem):
    destino_dir = os.path.join(settings.MEDIA_ROOT, 'xmls')
    os.makedirs(destino_dir, exist_ok=True)
    destino = os.path.join(destino_dir, os.path.basename(nome_arquivo))
    shutil.copyfile(origem, destino)
    return destino

def _salvar_arquivo_pgdas_local(nome_arquivo, origem):
    destino_dir = os.path.join(settings.MEDIA_ROOT, 'pgdas')
    os.makedirs(destino_dir, exist_ok=True)
    destino = os.path.join(destino_dir, os.path.basename(nome_arquivo))
    shutil.copyfile(origem, destino)
    return destino