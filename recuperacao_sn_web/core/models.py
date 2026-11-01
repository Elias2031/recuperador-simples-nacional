from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal
from django.conf import settings
import os

# Já existentes
class Empresa(models.Model):
    conta = models.ForeignKey("core.Conta", on_delete=models.CASCADE, related_name="empresas")

    cnpj = models.CharField(max_length=14)
    razao_social = models.CharField(max_length=200)
    nome_fantasia = models.CharField(max_length=200, blank=True, default="")

    inscricao_estadual = models.CharField(max_length=30, blank=True, default="")

    class Regime(models.TextChoices):
        SN = "SN", "Simples Nacional"
        PRESUMIDO = "PRESUMIDO", "Lucro Presumido"
        REAL = "REAL", "Lucro Real"
        OUTRO = "OUTRO", "Outro/Não informado"

    regime_tributario = models.CharField(
        max_length=15, choices=Regime.choices, default=Regime.OUTRO
    )

    cep = models.CharField(max_length=8, blank=True, default="")
    endereco = models.CharField(max_length=250, blank=True, default="")
    numero = models.CharField(max_length=20, blank=True, default="")
    bairro = models.CharField(max_length=120, blank=True, default="")
    municipio = models.CharField(max_length=120, blank=True, default="")
    uf = models.CharField(max_length=2, blank=True, default="")
    data_abertura = models.DateField(null=True, blank=True)

    cnae_principal = models.TextField(blank=True, default="")
    cnaes_secundarios = models.TextField(blank=True, default="")

    ativa = models.BooleanField(default=True)
    criada_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("conta", "cnpj")

    def __str__(self):
        return f"{self.razao_social} ({self.cnpj})"

class Competencia(models.Model):
    mes = models.IntegerField()
    ano = models.IntegerField()

    class Meta:
        unique_together = ('mes', 'ano')

    def __str__(self):
        return f"{self.mes:02d}/{self.ano}"

class ApuracaoFiscal(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    competencia = models.ForeignKey(Competencia, on_delete=models.CASCADE)
    criado_em = models.DateTimeField(auto_now_add=True)
    pgdas = models.OneToOneField(
        'PgdasValorDeclarado',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='apuracao'
    )

    valor_total_nfe = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    num_itens_processados = models.IntegerField(default=0)

    valor_das_teorico = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    valor_das_pago = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    valor_imposto_cheio = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    valor_irrecuperavel = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    valor_pis_novo = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    valor_cofins_novo = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    valor_icms_novo = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    credito_total_apurado = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    # Bases de cálculo
    base_icms_imune_ou_isento = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    base_icms_tributado = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    base_icms_ST_e_monofasico = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    base_icms_ST = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    # Cálculo dos tributos sobre essas bases
    icms_imune_ou_isento = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    icms_tributado = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    icms_ST_e_pis_cofins_monofasico = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    icms_ST = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    # Alíquotas
    aliquota_efetiva = models.DecimalField(max_digits=6, decimal_places=4, default=0)
    aliquota_icms = models.DecimalField(max_digits=6, decimal_places=4, default=0)
    aliquota_pis = models.DecimalField(max_digits=6, decimal_places=4, default=0)
    aliquota_cofins = models.DecimalField(max_digits=6, decimal_places=4, default=0)
    aliquota_irpj = models.DecimalField(max_digits=6, decimal_places=4, default=0)
    aliquota_csll = models.DecimalField(max_digits=6, decimal_places=4, default=0)
    aliquota_cpp = models.DecimalField(max_digits=6, decimal_places=4, default=0)
    
    icms_recuperado = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal('0.00'),
        verbose_name='ICMS Recuperado'
    )
    pis_recuperado = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal('0.00'),
        verbose_name='PIS Recuperado'
    )
    cofins_recuperado = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal('0.00'),
        verbose_name='COFINS Recuperado'
    )
    
    bloco_sem_st = models.JSONField(blank=True, null=True)
    bloco_com_st = models.JSONField(blank=True, null=True)
    bloco_total_tributos = models.JSONField(blank=True, null=True)
    
    faixa = models.PositiveSmallIntegerField(null=True, blank=True)
    limite_superior_faixa = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    aliquota_faixa = models.DecimalField(max_digits=5, decimal_places=4, null=True, blank=True)
    deducao_faixa = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    ultrapassa_limite = models.BooleanField(default=False)


    def __str__(self):
        return f"{self.empresa.razao_social} - {self.competencia}"


class NotaFiscal(models.Model):
    STATUS_CHOICES = [
        ('AUTORIZADA', 'Autorizada'),
        ('CANCELADA', 'Cancelada'),
    ]

    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    apuracao = models.ForeignKey(ApuracaoFiscal, on_delete=models.SET_NULL, null=True, blank=True)

    chave = models.CharField(max_length=44, unique=True, blank=False, null=False)
    numero = models.CharField(max_length=20)
    serie = models.CharField(max_length=10)
    data_emissao = models.DateField()
    valor_total = models.DecimalField(max_digits=15, decimal_places=2)
    
    tipo = models.CharField(
        max_length=20,
        choices=[
            ('entrada', 'Entrada'),
            ('saida', 'Saída'),
            ('cte', 'CT-e'),
            ('devolucao', 'Devolução'),
        ]
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='AUTORIZADA'
    )

    arquivo_xml = models.FileField(upload_to='xmls/', null=True, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"NF {self.numero} - {self.empresa.razao_social}"


class ItemNotaFiscal(models.Model):
    nota = models.ForeignKey(NotaFiscal, on_delete=models.CASCADE, related_name='itens')

    # Dados do produto
    codigo_produto = models.CharField(max_length=60, blank=True, null=True)
    descricao = models.CharField(max_length=255)
    ean = models.CharField(max_length=20, blank=True, null=True)
    ean_tributavel = models.CharField(max_length=20, blank=True, null=True)
    unidade = models.CharField(max_length=10)
    unidade_tributavel = models.CharField(max_length=10, blank=True, null=True)
    quantidade = models.DecimalField(max_digits=15, decimal_places=4, default=0)
    quantidade_tributavel = models.DecimalField(max_digits=15, decimal_places=4, blank=True, null=True)
    valor_unitario = models.DecimalField(max_digits=15, decimal_places=6, default=0)
    valor_unitario_tributavel = models.DecimalField(max_digits=15, decimal_places=6, blank=True, null=True)
    valor_produto = models.DecimalField(max_digits=15, decimal_places=2)
    base_calculo = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    ncm = models.CharField(max_length=10)
    cest = models.CharField(max_length=10, blank=True, null=True)
    cfop = models.CharField(max_length=10, blank=True, null=True)

    # Tributação geral
    cst_original = models.CharField(max_length=5, blank=True, null=True)
    origem = models.CharField(max_length=2, blank=True, null=True)
    vTotTrib = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)

    # ICMS detalhado
    icms_cst = models.CharField(max_length=5, blank=True, null=True)
    icms_mod_bc = models.CharField(max_length=5, blank=True, null=True)
    icms_vbc = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    icms_picms = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    icms_vicms = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)

    # PIS
    pis_cst = models.CharField(max_length=5, blank=True, null=True)
    pis_vbc = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    pis_ppis = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    pis_vpis = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)

    # COFINS
    cofins_cst = models.CharField(max_length=5, blank=True, null=True)
    cofins_vbc = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    cofins_pcofins = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    cofins_vcofins = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)

    # NCM vinculado
    ncm_analisado = models.ForeignKey('NcmUnico', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.descricao} - {self.ncm}"

class Participante(models.Model):
    cnpj = models.CharField(max_length=18)
    nome = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.nome} ({self.cnpj})"

class NotaParticipante(models.Model):
    nota = models.ForeignKey(NotaFiscal, on_delete=models.CASCADE)
    participante = models.ForeignKey(Participante, on_delete=models.CASCADE)
    tipo = models.CharField(max_length=20, choices=[
        ('emitente', 'Emitente'),
        ('destinatario', 'Destinatário'),
    ])

    def __str__(self):
        return f"{self.tipo} - {self.participante.nome}"

class UploadLote(models.Model):
    STATUS_CHOICES = [
        ('AGUARDANDO', 'Aguardando'),
        ('CONCLUIDO', 'Concluído'),
        ('ERRO', 'Erro'),
    ]

    empresa = models.ForeignKey('Empresa', on_delete=models.CASCADE)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    data_envio = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='AGUARDANDO')
    observacao = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Lote {self.id} - {self.empresa.nome}"
    
class ArquivoImportado(models.Model):
    upload_lote = models.ForeignKey(UploadLote, related_name='arquivos', on_delete=models.CASCADE)
    nome_arquivo = models.CharField(max_length=255)
    tipo = models.CharField(max_length=10)  # XML, ZIP, PDF
    status = models.CharField(max_length=20, choices=[('OK', 'Sucesso'), ('ERRO', 'Erro'), ('IGNORADO', 'Ignorado')])
    mensagem = models.TextField(blank=True, null=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nome_arquivo

class PgdasValorDeclarado(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    competencia = models.ForeignKey(Competencia, on_delete=models.CASCADE)
    arquivo_pdf = models.FileField(upload_to='pgdas/', null=True, blank=True)

    receita_bruta = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    valor_rbt12 = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    valor_IRPJ_pago_original = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    valor_CSLL_pago_original = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    valor_COFINS_pago_original = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    valor_PIS_pago_original = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    valor_INSS_pago_original = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    valor_ICMS_pago_original = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    valor_IPI_pago_original = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    valor_ISS_pago_original = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    valor_DAS_pago_original = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.empresa.nome} - {self.competencia}"
    
class NcmUnico(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    ncm = models.CharField(max_length=10)
    nome_item = models.CharField(max_length=255, blank=True, null=True)
    desc_tipi = models.TextField(blank=True, null=True)
    descricao_st = models.TextField(blank=True, null=True)

    aliquota_icms_retornado = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    descricao_icms_retornado = models.TextField(blank=True, null=True)
    base_legal_icms_retornado = models.TextField(blank=True, null=True)
    vigencia_inicial_icms = models.DateField(blank=True, null=True)
    observacao_icms = models.TextField(blank=True, null=True)
    cst_icms = models.CharField(max_length=5, blank=True, null=True)

    cest = models.CharField(max_length=10, blank=True, null=True)
    descricao_ncm_st = models.TextField(blank=True, null=True)
    base_legal_st = models.TextField(blank=True, null=True)
    vigencia_inicial_st = models.DateField(blank=True, null=True)
    observacao_st = models.TextField(blank=True, null=True)
    segmentos_st = models.TextField(blank=True, null=True)

    mva = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    mva_ajustada_4 = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    mva_ajustada_7 = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    mva_ajustada_12 = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)

    cst_simples_pis_cofins = models.CharField(max_length=10, blank=True, null=True)
    base_legal_pis_cofins = models.TextField(blank=True, null=True)

    cest_st_interestadual = models.CharField(max_length=10, blank=True, null=True)
    descricao_st_interestadual = models.TextField(blank=True, null=True)
    segmento_st_interestadual = models.TextField(blank=True, null=True)
    mva_original_st_interestadual = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    mva_ajustada_4_st_interestadual = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    mva_ajustada_12_st_interestadual = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)

    vigencia_inicial_st_interestadual = models.DateField(blank=True, null=True)
    base_legal_st_interestadual = models.TextField(blank=True, null=True)
    base_legal_interna_st_interestadual = models.TextField(blank=True, null=True)

    aplicabilidade_st_interestadual = models.TextField(blank=True, null=True)
    nao_aplicabilidade_st_interestadual = models.TextField(blank=True, null=True)
    
    ncm_foi_analisado = models.BooleanField(default=False)

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('empresa', 'ncm')
        ordering = ['ncm']

    def __str__(self):
        return f"{self.ncm} - {self.empresa.nome}"
