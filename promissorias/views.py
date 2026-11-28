import hashlib
import hmac
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from decouple import config
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import Q, Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_GET

from promissorias.models import AcordoPromissoria, ClientePromissoria, ParcelaPromissoria
from django.db import transaction
import random
import time

def _chave_pix_config() -> str:
    return config("CHAVE_PIX_LOJA", default="").strip()


TEMPLATES_COBRANCA = {
    "vence_hoje": [
        (
            "Olá, {nome}! Tudo bem? Passando para lembrar que a parcela {parcela} "
            "({descricao}), no valor de R$ {valor}, vence hoje ({vencimento}). "
            "Se precisar de algo, é só chamar por aqui!"
        ),
        (
            "Oi, {nome}! Um lembrete rápido: hoje ({vencimento}) é o vencimento da "
            "parcela {parcela} referente a {descricao}, no valor de R$ {valor}. "
            "Qualquer dúvida, estamos à disposição."
        ),
        (
            "Bom dia/boa tarde, {nome}! Tudo certo? Só avisando que a parcela {parcela} "
            "de {descricao} (R$ {valor}) vence na data de hoje, {vencimento}. "
            "Agradecemos pela preferência!"
        ),
        (
            "Olá, {nome}. Lembrando que vence hoje ({vencimento}) a parcela {parcela} "
            "da sua compra ({descricao}), totalizando R$ {valor}. "
            "Caso já tenha efetuado o pagamento, por favor desconsidere."
        ),
    ],
    "atraso_1_a_5_dias": [
        (
            "Olá, {nome}, tudo bem? Consta em nosso sistema que a parcela {parcela} "
            "({descricao}), no valor de R$ {valor} com vencimento em {vencimento}, "
            "está em aberto há {dias} {dia_txt}. Podemos confirmar o pagamento para hoje?"
        ),
        (
            "Oi, {nome}! Passando para avisar que a parcela {parcela} de {descricao} "
            "(R$ {valor}), vencida no dia {vencimento} ({dias} {dia_txt} atrás), "
            "ainda não consta como paga. Consegue regularizar por aí?"
        ),
        (
            "Olá, {nome}. Identificamos uma pendência na parcela {parcela} ({descricao}), "
            "no valor de R$ {valor}, que venceu em {vencimento} (atraso de {dias} {dia_txt}). "
            "Se já pagou, nos envie o comprovante para darmos baixa."
        ),
        (
            "Tudo bem, {nome}? Notamos que a parcela {parcela} referente a {descricao}, "
            "de R$ {valor} e vencimento em {vencimento}, segue em aberto há {dias} {dia_txt}. "
            "Ficamos no aguardo para regularizar."
        ),
    ],
    "encaminhamento_serasa": [
        (
            "Olá, {nome}. A parcela {parcela} ({descricao}), no valor de R$ {valor} "
            "e vencida em {vencimento} ({dias} dias de atraso), permanece em aberto. "
            "Para evitar o encaminhamento do débito ao Serasa, pedimos que regularize ou entre em contato."
        ),
        (
            "Aviso importante, {nome}: consta em aberto a parcela {parcela} de {descricao} "
            "(R$ {valor}), vencida há {dias} dias ({vencimento}). Evite restrições no CPF "
            "e o envio ao Serasa acertando essa pendência conosco."
        ),
        (
            "Olá, {nome}. Ainda não identificamos o pagamento da parcela {parcela} ({descricao}), "
            "de R$ {valor}, vencida em {vencimento} ({dias} dias em atraso). "
            "Caso não seja regularizada, o título seguirá para negativação no Serasa. Fale conosco."
        ),
        (
            "Prezado(a) {nome}, a parcela {parcela} referente a {descricao}, no valor de R$ {valor} "
            "(vencimento {vencimento} · {dias} dias de atraso), segue pendente. "
            "Entre em contato para evitarmos o registro do débito junto ao Serasa."
        ),
    ],
}

RODAPES_PIX = [
    "Para facilitar, segue abaixo nossa chave Pix (basta copiar e colar):",
    "Se preferir pagar via Pix agora, vou mandar a chave na mensagem seguinte para facilitar a cópia:",
    "Caso queira quitar por Pix, segue a chave logo abaixo:",
    "Para pagamento via Pix, é só copiar a chave que enviei logo abaixo:",
]
def _gateway_config() -> tuple[str, str, str]:
    base_url = config("AVISEJA_BASE_URL", default="").strip().rstrip("/")
    slug = config("AVISEJA_INSTANCE_ID", default="default").strip()
    secret = config("AVISEJA_HMAC_SECRET", default="").strip()
    return base_url, slug, secret


def _assinar_hmac(secret: str, raw_body: bytes) -> str:
    return hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()


def _chamar_gateway_get(path: str, params: dict, secret: str, timeout: int = 10) -> tuple[int, dict]:
    base_url, _, _ = _gateway_config()
    if not base_url:
        return 503, {"status": "erro", "mensagem": "Gateway WhatsApp ainda não configurado."}
    if not secret:
        return 500, {"status": "erro", "mensagem": "WHATSAPP_HMAC_SECRET não configurado."}

    query = urllib.parse.urlencode(params)
    url = f"{base_url}{path}?{query}" if query else f"{base_url}{path}"
    sig = _assinar_hmac(secret, b"")

    req = urllib.request.Request(
        url,
        method="GET",
        headers={"X-Signature": sig},
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
            return resp.status, payload
    except urllib.error.HTTPError as exc:
        try:
            payload = json.loads(exc.read().decode("utf-8"))
        except Exception:
            payload = {"status": "erro", "mensagem": f"HTTP {exc.code}"}
        return exc.code, payload
    except urllib.error.URLError as exc:
        return 502, {
            "status": "erro",
            "mensagem": f"Não foi possível falar com o gateway WhatsApp: {exc.reason}",
        }
    except Exception as exc:
        return 500, {"status": "erro", "mensagem": f"Erro ao consultar gateway: {exc}"}


@staff_member_required(login_url='login')
@require_GET
def whatsapp_qrcode(request):
    base_url, slug, secret = _gateway_config()
    if not base_url:
        return JsonResponse(
            {"status": "erro", "mensagem": "Gateway WhatsApp ainda não configurado."},
            status=503,
        )

    acao = request.GET.get("acao", "gerar")
    endpoint = "/qrcode" if acao == "status" else "/qrcode/gerar"
    code, payload = _chamar_gateway_get(endpoint, {"slug": slug}, secret, timeout=15)
    return JsonResponse(payload, status=code)


@staff_member_required(login_url='login')
@require_GET
def whatsapp_status(request):
    base_url, slug, secret = _gateway_config()
    if not base_url:
        return JsonResponse(
            {"status": "erro", "conectado": False, "mensagem": "Gateway WhatsApp ainda não configurado."},
            status=503,
        )

    code, payload = _chamar_gateway_get("/sessao/status", {"slug": slug}, secret, timeout=10)
    return JsonResponse(payload, status=code)


def _apenas_digitos(valor):
    return re.sub(r"\D", "", valor or "")


def _formatar_moeda_br(valor: Decimal) -> str:
    return f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def _montar_mensagem_cobranca(
    parcela: ParcelaPromissoria, hoje: date, indice_variacao: int | None = None
) -> tuple[str, str, int]:
    dias_atraso = max(0, (hoje - parcela.vencimento).days)
    cliente = parcela.acordo.cliente
    primeiro_nome = (cliente.nome or "").strip().split()[0] if cliente.nome else "Cliente"
    valor_fmt = _formatar_moeda_br(parcela.valor)
    venc_fmt = parcela.vencimento.strftime("%d/%m/%Y")
    descricao = parcela.acordo.descricao or "compra na loja"
    identificacao = parcela.identificacao_parcela

    if dias_atraso == 0:
        faixa = "vence_hoje"
    elif 1 <= dias_atraso <= 5:
        faixa = "atraso_1_a_5_dias"
    else:
        faixa = "encaminhamento_serasa"

    modelos = TEMPLATES_COBRANCA[faixa]
    idx = (indice_variacao if indice_variacao is not None else parcela.id) % len(modelos)
    dia_txt = "dia" if dias_atraso == 1 else "dias"

    mensagem = modelos[idx].format(
        nome=primeiro_nome,
        parcela=identificacao,
        descricao=descricao,
        valor=valor_fmt,
        vencimento=venc_fmt,
        dias=dias_atraso,
        dia_txt=dia_txt,
    )

    if _chave_pix_config():
        rodape_idx = (idx + parcela.id) % len(RODAPES_PIX)
        mensagem = f"{mensagem}\n\n{RODAPES_PIX[rodape_idx]}"

    return mensagem, faixa, dias_atraso

def _chamar_gateway_enviar(telefone: str, mensagem: str) -> tuple[bool, str]:
    base_url, slug, secret = _gateway_config()
    if not base_url:
        return False, "Envio automático ainda não configurado."
    if not secret:
        return False, "WHATSAPP_HMAC_SECRET não configurado."

    url = f"{base_url}/enviar"
    payload = {
        "slug": slug,
        "telefone": telefone,
        "mensagem": mensagem,
    }
    raw_body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    sig = _assinar_hmac(secret, raw_body)

    req = urllib.request.Request(
        url,
        data=raw_body,
        headers={
            "Content-Type": "application/json",
            "X-Signature": sig,
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=130) as resp:
            dados = json.loads(resp.read().decode("utf-8"))
            if resp.status == 200 and dados.get("status") == "enviado":
                return True, ""
            return False, dados.get("mensagem") or f"Status {resp.status}"
    except urllib.error.HTTPError as exc:
        try:
            detalhe = exc.read().decode("utf-8")
        except Exception:
            detalhe = str(exc)
        return False, f"HTTP {exc.code}: {detalhe}"
    except Exception as exc:
        return False, f"Falha ao falar com gateway: {exc}"


def _disparar_aviso_parcela_agora(
    parcela: ParcelaPromissoria, hoje: date, indice_variacao: int | None = None
) -> tuple[bool, str]:
    telefone = _apenas_digitos(parcela.acordo.cliente.whatsapp)
    if not telefone:
        return False, "WhatsApp do cliente não informado."

    aviso_anterior = parcela.ultimo_aviso_em

    # Trava atômica no banco: só avança se ainda não foi avisado hoje
    with transaction.atomic():
        reservou = (
            ParcelaPromissoria.objects.filter(pk=parcela.pk)
            .exclude(status="pago")
            .filter(Q(ultimo_aviso_em__isnull=True) | ~Q(ultimo_aviso_em=hoje))
            .update(ultimo_aviso_em=hoje)
        )

    if reservou == 0:
        return False, "Aviso já enviado ou em processamento hoje."

    mensagem, _, _ = _montar_mensagem_cobranca(parcela, hoje, indice_variacao=indice_variacao)
    ok, erro = _chamar_gateway_enviar(telefone, mensagem)
    if not ok:
        # Se falhou antes de enviar, devolve o estado anterior para poder tentar de novo
        ParcelaPromissoria.objects.filter(pk=parcela.pk).update(ultimo_aviso_em=aviso_anterior)
        return False, erro

    chave_pix = _chave_pix_config()
    if chave_pix:
        time.sleep(random.uniform(3, 5))
        _chamar_gateway_enviar(telefone, chave_pix)

    if parcela.vencimento == hoje:
        ParcelaPromissoria.objects.filter(pk=parcela.pk).update(lembrete_vencimento_enviado=True)
        parcela.lembrete_vencimento_enviado = True

    parcela.ultimo_aviso_em = hoje
    return True, ""

def _descrever_envio_parcela(parcela: ParcelaPromissoria, hoje: date, falhou_hoje: bool = False) -> dict:
    dias_atraso = max(0, (hoje - parcela.vencimento).days)
    enviado_hoje = parcela.ultimo_aviso_em == hoje

    if parcela.status == "pago":
        return {
            "codigo": "pago",
            "estilo": "enviado",
            "titulo": "Sem envio (pago)",
            "detalhe": f"Pago em {parcela.pago_em.strftime('%d/%m/%Y')}" if parcela.pago_em else "Parcela quitada",
        }

    if falhou_hoje:
        return {
            "codigo": "falhou_hoje",
            "estilo": "falhou",
            "titulo": "Falhou no envio hoje",
            "detalhe": "Erro no disparo imediato",
        }

    if parcela.vencimento > hoje:
        return {
            "codigo": "aguardando_data",
            "estilo": "aguardando",
            "titulo": "Aguardando data",
            "detalhe": f"Entra no lote em {parcela.vencimento.strftime('%d/%m/%Y')}",
        }

    if parcela.vencimento == hoje:
        if enviado_hoje:
            return {
                "codigo": "enviado_hoje",
                "estilo": "enviado",
                "titulo": "Lembrete enviado hoje",
                "detalhe": f"Enviado em {parcela.ultimo_aviso_em.strftime('%d/%m/%Y')}",
            }
        return {
            "codigo": "aguardando_disparo",
            "estilo": "aguardando",
            "titulo": "Aguardando disparo hoje",
            "detalhe": "Vence hoje · lote das 18:30",
        }

    faixa_txt = f"{dias_atraso}d atraso (Serasa)" if dias_atraso > 7 else f"{dias_atraso}d atraso"
    if enviado_hoje:
        return {
            "codigo": "atrasado_enviado",
            "estilo": "enviado",
            "titulo": "Enviado hoje (atraso)",
            "detalhe": f"{faixa_txt} · aviso hoje",
        }

    return {
        "codigo": "atrasado_pendente",
        "estilo": "pendente",
        "titulo": "Não enviado hoje",
        "detalhe": f"{faixa_txt} · pendente no lote",
    }


def _paginar_seguro(queryset, por_pagina: int, page_param):
    paginator = Paginator(queryset, por_pagina)
    try:
        page_obj = paginator.page(page_param or 1)
    except (PageNotAnInteger, EmptyPage):
        page_obj = paginator.page(1)

    paginas = paginator.get_elided_page_range(
        page_obj.number, on_each_side=1, on_ends=1
    )
    return page_obj, paginas


def _qs_preservando(request, chave_pagina: str, numero_pagina: int) -> str:
    params = request.GET.copy()
    params[chave_pagina] = str(numero_pagina)
    return params.urlencode()


@staff_member_required(login_url='login')
def painel_promissorias(request):
    falha_parcela_id = request.session.pop("falha_envio_parcela_id", None)
    falha_data = request.session.pop("falha_envio_data", None)

    if request.method == "POST":
        acao = request.POST.get("acao")

        if acao == "nova_promissoria":
            try:
                valor_total = Decimal(request.POST.get("valor_total", "0").replace(",", "."))
                quantidade = int(request.POST.get("quantidade_parcelas", 1))
            except (InvalidOperation, ValueError):
                messages.error(request, "Valor ou quantidade de parcelas inválidos.")
                return redirect("painel_promissorias")

            if valor_total <= 0 or quantidade < 1:
                messages.error(request, "Informe um valor maior que zero e pelo menos 1 parcela.")
                return redirect("painel_promissorias")

            venc_str = request.POST.get("primeiro_vencimento")
            try:
                primeiro_vencimento = (
                    datetime.strptime(venc_str, "%Y-%m-%d").date() if venc_str else timezone.localdate()
                )
            except ValueError:
                messages.error(request, "Data do primeiro vencimento inválida.")
                return redirect("painel_promissorias")

            cpf_ja_existente = False
            cliente_id = request.POST.get("cliente_id")
            if cliente_id == "novo":
                nome = request.POST.get("novo_nome", "").strip()
                cpf = _apenas_digitos(request.POST.get("novo_cpf"))
                whatsapp = _apenas_digitos(request.POST.get("novo_whatsapp"))

                if not nome or not cpf:
                    messages.error(request, "Para um cliente novo, informe nome e CPF.")
                    return redirect("painel_promissorias")
                if not whatsapp:
                    messages.error(request, "WhatsApp inválido.")
                    return redirect("painel_promissorias")

                cliente, criado = ClientePromissoria.objects.get_or_create(
                    cpf_cnpj=cpf, defaults={"nome": nome, "whatsapp": whatsapp}
                )
                if not criado:
                    cpf_ja_existente = True
            else:
                try:
                    cliente = get_object_or_404(ClientePromissoria, id=int(cliente_id))
                except (TypeError, ValueError):
                    messages.error(request, "Cliente inválido.")
                    return redirect("painel_promissorias")

            acordo = AcordoPromissoria.objects.create(
                cliente=cliente,
                descricao=request.POST.get("descricao", "").strip() or "Compra na loja",
                valor_total=valor_total,
                quantidade_parcelas=quantidade,
                primeiro_vencimento=primeiro_vencimento,
            )

            primeira_paga = request.POST.get("primeira_parcela_paga") == "on"
            primeira_parcela = acordo.parcelas.order_by("numero_parcela").first()
            hoje = timezone.localdate()
            base_url, _, _ = _gateway_config()

            if primeira_parcela and primeira_paga:
                primeira_parcela.status = "pago"
                primeira_parcela.pago_em = timezone.now()
                primeira_parcela.save(update_fields=["status", "pago_em"])
            elif (
                not cpf_ja_existente
                and primeira_parcela
                and primeira_parcela.vencimento == hoje
                and base_url
            ):
                enviou, erro_wa = _disparar_aviso_parcela_agora(primeira_parcela, hoje)
                if enviou:
                    messages.info(request, "Lembrete de vencimento de hoje enviado via WhatsApp!")
                else:
                    request.session["falha_envio_parcela_id"] = primeira_parcela.id
                    request.session["falha_envio_data"] = hoje.isoformat()
                    messages.warning(
                        request,
                        f"Promissória criada, mas o envio imediato no WhatsApp falhou: {erro_wa}",
                    )

            if cpf_ja_existente:
                messages.info(
                    request,
                    f"CPF já cadastrado: promissória ({quantidade}x) criada no cadastro existente de {cliente.nome}. Disparo imediato pausado para conferência.",
                )
            else:
                messages.success(
                    request,
                    f"Promissória de {cliente.nome} ({quantidade}x) criada com sucesso!",
                )
            return redirect("painel_promissorias")

        elif acao == "baixar_parcela":
            parcela = get_object_or_404(ParcelaPromissoria, id=request.POST.get("parcela_id"))
            parcela.status = "pago"
            parcela.pago_em = timezone.now()
            parcela.save(update_fields=["status", "pago_em"])
            messages.success(request, f"Parcela {parcela.identificacao_parcela} baixada manualmente.")
            return redirect("painel_promissorias")

        elif acao == "quitar_tudo":
            cliente = get_object_or_404(ClientePromissoria, id=request.POST.get("cliente_id"))
            qtd = (
                ParcelaPromissoria.objects.filter(acordo__cliente=cliente)
                .exclude(status="pago")
                .update(status="pago", pago_em=timezone.now())
            )
            messages.success(request, f"{qtd} parcela(s) de {cliente.nome} quitada(s).")
            return redirect("painel_promissorias")

        elif acao == "editar_cliente":
            try:
                cliente = get_object_or_404(ClientePromissoria, id=int(request.POST.get("cliente_id")))
            except (TypeError, ValueError):
                messages.error(request, "Cliente inválido.")
                return redirect("painel_promissorias")

            novo_nome = request.POST.get("nome", "").strip()
            novo_cpf = _apenas_digitos(request.POST.get("cpf_cnpj"))
            novo_whatsapp = _apenas_digitos(request.POST.get("whatsapp")) or cliente.whatsapp
            novo_obs = request.POST.get("observacoes", "").strip() or None

            if not novo_nome or not novo_cpf:
                messages.error(request, "Nome e CPF/CNPJ são obrigatórios.")
                return redirect("painel_promissorias")

            if ClientePromissoria.objects.exclude(pk=cliente.pk).filter(cpf_cnpj=novo_cpf).exists():
                messages.error(request, "Já existe outro cliente cadastrado com esse CPF/CNPJ.")
                return redirect("painel_promissorias")

            cliente.nome = novo_nome
            cliente.cpf_cnpj = novo_cpf
            cliente.whatsapp = novo_whatsapp
            cliente.observacoes = novo_obs
            cliente.save()
            messages.success(request, f"Cadastro de {cliente.nome} atualizado.")
            return redirect("painel_promissorias")
        
        elif acao == "excluir_parcela":
            parcela = get_object_or_404(ParcelaPromissoria, id=request.POST.get("parcela_id"))
            with transaction.atomic():
                desc = f"{parcela.acordo.cliente.nome} ({parcela.identificacao_parcela})"
                parcela.delete()
            messages.success(request, f"Parcela {desc} excluída permanentemente.")
            return redirect("painel_promissorias")
        
    hoje = timezone.localdate()

    parcelas_qs = (
        ParcelaPromissoria.objects.select_related("acordo", "acordo__cliente")
        .order_by("vencimento", "numero_parcela", "id")
    )
    parcelas_page, paginas_parcelas = _paginar_seguro(
        parcelas_qs, 25, request.GET.get("p_page")
    )
    parcelas = list(parcelas_page.object_list)
    for p in parcelas:
        falhou_hoje = bool(
            falha_parcela_id == p.id and falha_data == hoje.isoformat() and p.ultimo_aviso_em != hoje
        )
        p.info_envio = _descrever_envio_parcela(p, hoje, falhou_hoje=falhou_hoje)

    total_pendente = (
        ParcelaPromissoria.objects.exclude(status="pago").aggregate(t=Sum("valor"))["t"] or Decimal("0.00")
    )
    total_recebido = (
        ParcelaPromissoria.objects.filter(status="pago").aggregate(t=Sum("valor"))["t"] or Decimal("0.00")
    )

    clientes_qs = (
        ClientePromissoria.objects.annotate(
            saldo_devedor=Sum(
                "acordos__parcelas__valor",
                filter=~Q(acordos__parcelas__status="pago"),
            )
        )
        .prefetch_related("acordos__parcelas")
        .order_by("nome", "id")
    )
    clientes_page, paginas_clientes = _paginar_seguro(
        clientes_qs, 15, request.GET.get("c_page")
    )

    links_parcelas = [
        {
            "num": num,
            "is_ellipsis": num == parcelas_page.paginator.ELLIPSIS,
            "active": num == parcelas_page.number,
            "url": f"?{_qs_preservando(request, 'p_page', num)}#parcelas"
            if num != parcelas_page.paginator.ELLIPSIS
            else "",
        }
        for num in paginas_parcelas
    ]

    links_clientes = [
        {
            "num": num,
            "is_ellipsis": num == clientes_page.paginator.ELLIPSIS,
            "active": num == clientes_page.number,
            "url": f"?{_qs_preservando(request, 'c_page', num)}#clientes"
            if num != clientes_page.paginator.ELLIPSIS
            else "",
        }
        for num in paginas_clientes
    ]

    return render(
        request,
        "painel.html",
        {
            "parcelas": parcelas,
            "parcelas_page": parcelas_page,
            "links_parcelas": links_parcelas,
            "url_parcelas_prev": f"?{_qs_preservando(request, 'p_page', parcelas_page.previous_page_number())}#parcelas"
            if parcelas_page.has_previous()
            else "",
            "url_parcelas_next": f"?{_qs_preservando(request, 'p_page', parcelas_page.next_page_number())}#parcelas"
            if parcelas_page.has_next()
            else "",
            "clientes": clientes_page.object_list,
            "clientes_page": clientes_page,
            "links_clientes": links_clientes,
            "url_clientes_prev": f"?{_qs_preservando(request, 'c_page', clientes_page.previous_page_number())}#clientes"
            if clientes_page.has_previous()
            else "",
            "url_clientes_next": f"?{_qs_preservando(request, 'c_page', clientes_page.next_page_number())}#clientes"
            if clientes_page.has_next()
            else "",
            "hoje": hoje,
            "total_pendente": total_pendente,
            "total_recebido": total_recebido,
        },
    )

@staff_member_required(login_url='login')
def clientes_promissorias(request):
    if request.method == "POST":
        acao = request.POST.get("acao")

        if acao == "baixar_parcela":
            parcela = get_object_or_404(ParcelaPromissoria, id=request.POST.get("parcela_id"))
            parcela.status = "pago"
            parcela.pago_em = timezone.now()
            parcela.save(update_fields=["status", "pago_em"])
            messages.success(request, f"Parcela {parcela.identificacao_parcela} baixada manualmente.")
            return redirect("clientes")

        elif acao == "excluir_parcela":
            parcela = get_object_or_404(
                ParcelaPromissoria.objects.select_related("acordo__cliente"),
                id=request.POST.get("parcela_id"),
            )
            with transaction.atomic():
                desc = f"{parcela.acordo.cliente.nome} ({parcela.identificacao_parcela})"
                parcela.delete()
            messages.success(request, f"Parcela {desc} excluída.")
            return redirect("clientes")

        elif acao == "excluir_acordo":
            acordo = get_object_or_404(
                AcordoPromissoria.objects.select_related("cliente"),
                id=request.POST.get("acordo_id"),
            )
            with transaction.atomic():
                nome_cli = acordo.cliente.nome
                acordo.delete()
            messages.success(request, f"Promissória/acordo de {nome_cli} e suas parcelas excluídos.")
            return redirect("clientes")

        elif acao == "excluir_cliente_tudo":
            cliente = get_object_or_404(ClientePromissoria, id=request.POST.get("cliente_id"))
            with transaction.atomic():
                nome_cli = cliente.nome
                cliente.delete()
            messages.success(request, f"Cliente {nome_cli} e todos os acordos/parcelas vinculados foram excluídos.")
            return redirect("clientes")

        elif acao == "quitar_tudo":
            cliente = get_object_or_404(ClientePromissoria, id=request.POST.get("cliente_id"))
            qtd = (
                ParcelaPromissoria.objects.filter(acordo__cliente=cliente)
                .exclude(status="pago")
                .update(status="pago", pago_em=timezone.now())
            )
            messages.success(request, f"{qtd} parcela(s) de {cliente.nome} quitada(s).")
            return redirect("clientes")

        elif acao == "editar_cliente":
            try:
                cliente = get_object_or_404(ClientePromissoria, id=int(request.POST.get("cliente_id")))
            except (TypeError, ValueError):
                messages.error(request, "Cliente inválido.")
                return redirect("clientes")

            novo_nome = request.POST.get("nome", "").strip()
            novo_cpf = _apenas_digitos(request.POST.get("cpf_cnpj"))
            novo_whatsapp = _apenas_digitos(request.POST.get("whatsapp")) or cliente.whatsapp
            novo_obs = request.POST.get("observacoes", "").strip() or None

            if not novo_nome or not novo_cpf:
                messages.error(request, "Nome e CPF/CNPJ são obrigatórios.")
                return redirect("clientes")

            if ClientePromissoria.objects.exclude(pk=cliente.pk).filter(cpf_cnpj=novo_cpf).exists():
                messages.error(request, "Já existe outro cliente cadastrado com esse CPF/CNPJ.")
                return redirect("clientes")

            cliente.nome = novo_nome
            cliente.cpf_cnpj = novo_cpf
            cliente.whatsapp = novo_whatsapp
            cliente.observacoes = novo_obs
            cliente.save()
            messages.success(request, f"Cadastro de {cliente.nome} atualizado.")
            return redirect("clientes")

    hoje = timezone.localdate()
    clientes_qs = (
        ClientePromissoria.objects.annotate(
            saldo_devedor=Sum(
                "acordos__parcelas__valor",
                filter=~Q(acordos__parcelas__status="pago"),
            )
        )
        .prefetch_related("acordos__parcelas")
        .order_by("nome", "id")
    )
    clientes_page, paginas_clientes = _paginar_seguro(
        clientes_qs, 15, request.GET.get("c_page")
    )

    links_clientes = [
        {
            "num": num,
            "is_ellipsis": num == clientes_page.paginator.ELLIPSIS,
            "active": num == clientes_page.number,
            "url": f"?{_qs_preservando(request, 'c_page', num)}",
        }
        for num in paginas_clientes
    ]

    return render(
        request,
        "clientes.html",
        {
            "clientes": clientes_page.object_list,
            "clientes_page": clientes_page,
            "links_clientes": links_clientes,
            "url_clientes_prev": f"?{_qs_preservando(request, 'c_page', clientes_page.previous_page_number())}"
            if clientes_page.has_previous()
            else "",
            "url_clientes_next": f"?{_qs_preservando(request, 'c_page', clientes_page.next_page_number())}"
            if clientes_page.has_next()
            else "",
            "hoje": hoje,
        },
    )