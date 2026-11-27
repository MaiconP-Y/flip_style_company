import random
import time

from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils import timezone

from promissorias.models import ParcelaPromissoria
from promissorias.views import (
    _apenas_digitos,
    _chave_pix_config,
    _disparar_aviso_parcela_agora,
    _gateway_config,
    _montar_mensagem_cobranca,
)


class Command(BaseCommand):
    help = "Dispara de forma síncrona (um por vez) as cobranças de promissórias pendentes do dia."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Simula sem enviar no WhatsApp nem alterar o banco.",
        )

    def handle(self, *args, **options):
        base_url, _, _ = _gateway_config()
        dry_run = options["dry_run"]

        if not dry_run and not base_url:
            self.stderr.write(self.style.ERROR("Gateway não configurado."))
            return

        hoje = timezone.localdate()
        chave_pix = _chave_pix_config()

        parcelas = list(
            ParcelaPromissoria.objects.select_related("acordo", "acordo__cliente")
            .exclude(status="pago")
            .filter(vencimento__lte=hoje)
            .filter(Q(ultimo_aviso_em__isnull=True) | ~Q(ultimo_aviso_em=hoje))
            .order_by("vencimento", "numero_parcela", "id")
        )

        total = len(parcelas)
        if total == 0:
            self.stdout.write("Nenhuma cobrança pendente hoje.")
            return

        for idx, parcela in enumerate(parcelas, start=1):
            telefone = _apenas_digitos(parcela.acordo.cliente.whatsapp)
            if not telefone:
                self.stderr.write(f"[{idx}/{total}] Parcela #{parcela.id} sem WhatsApp.")
                continue

            if dry_run:
                mensagem, _, _ = _montar_mensagem_cobranca(parcela, hoje, indice_variacao=idx)
                self.stdout.write(f"[DRY-RUN {idx}/{total}] -> {telefone}: {mensagem}")
                if chave_pix:
                    self.stdout.write(f"[DRY-RUN {idx}/{total} PIX] -> {telefone}: {chave_pix}")
            else:
                enviou, erro_wa = _disparar_aviso_parcela_agora(parcela, hoje, indice_variacao=idx)
                if enviou:
                    self.stdout.write(f"[{idx}/{total}] Enviado para {telefone}.")
                else:
                    self.stderr.write(f"[{idx}/{total}] Falha em {telefone}: {erro_wa}")

            if idx < total and not dry_run:
                time.sleep(random.uniform(20, 50))