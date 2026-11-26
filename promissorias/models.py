from datetime import date
from dateutil.relativedelta import relativedelta
from django.db import models


class ClientePromissoria(models.Model):
    nome = models.CharField(max_length=150)
    cpf_cnpj = models.CharField(
        max_length=18,
        unique=True,
        verbose_name="CPF ou CNPJ",
        help_text="Obrigatório para emissão de boleto e identificação.",
    )
    whatsapp = models.CharField(
        max_length=20,
        help_text="Formato: 5543999999999",
    )
    observacoes = models.TextField(blank=True, null=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Cliente (Promissória)"
        verbose_name_plural = "Clientes (Promissórias)"
        ordering = ['nome']

    def __str__(self):
        return f"{self.nome} - {self.cpf_cnpj}"


class AcordoPromissoria(models.Model):
    cliente = models.ForeignKey(
        ClientePromissoria,
        on_delete=models.CASCADE,
        related_name='acordos',
    )
    descricao = models.CharField(
        max_length=200,
        blank=True,
        default="Compra na loja",
        help_text="Ex: Conjunto moletom + boné",
    )
    valor_total = models.DecimalField(max_digits=10, decimal_places=2)
    quantidade_parcelas = models.PositiveIntegerField(default=1)
    primeiro_vencimento = models.DateField(default=date.today)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Promissória / Acordo"
        verbose_name_plural = "Promissórias / Acordos"

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)

        if is_new:
            qtd = max(1, int(self.quantidade_parcelas or 1))
            valor_parcela = round(self.valor_total / qtd, 2)
            diferenca = self.valor_total - (valor_parcela * qtd)

            for i in range(qtd):
                valor_atual = valor_parcela + (diferenca if i == 0 else 0)
                vencimento_atual = self.primeiro_vencimento + relativedelta(months=i)

                ParcelaPromissoria.objects.create(
                    acordo=self,
                    numero_parcela=i + 1,
                    total_parcelas=qtd,
                    valor=valor_atual,
                    vencimento=vencimento_atual,
                )

    def __str__(self):
        return f"{self.cliente.nome} - R$ {self.valor_total} ({self.quantidade_parcelas}x)"


class ParcelaPromissoria(models.Model):
    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('pago', 'Pago'),
        ('atrasado', 'Atrasado'),
    ]

    acordo = models.ForeignKey(
        AcordoPromissoria,
        on_delete=models.CASCADE,
        related_name='parcelas',
    )
    numero_parcela = models.PositiveIntegerField()
    total_parcelas = models.PositiveIntegerField()
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    vencimento = models.DateField(db_index=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pendente',
        db_index=True,
    )

    # Controle de disparos WhatsApp
    lembrete_vencimento_enviado = models.BooleanField(default=False)
    ultimo_aviso_em = models.DateField(blank=True, null=True, db_index=True)
    pago_em = models.DateTimeField(blank=True, null=True)

    class Meta:
        verbose_name = "Parcela"
        verbose_name_plural = "Parcelas"
        ordering = ['vencimento', 'numero_parcela']

    @property
    def identificacao_parcela(self):
        return f"{self.numero_parcela}/{self.total_parcelas}"

    def __str__(self):
        return f"{self.acordo.cliente.nome} ({self.identificacao_parcela}) - R$ {self.valor}"