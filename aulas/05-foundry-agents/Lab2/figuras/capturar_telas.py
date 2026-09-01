"""Captura as telas reais da aplicação para o material da aula.

Sobe nada: só fotografa o que já está rodando em http://localhost:8501.
Rode depois de `docker compose up` ou dos dois processos locais.

    python figuras/capturar_telas.py
"""
import asyncio
import os

from playwright.async_api import async_playwright

WEB = os.getenv("DEVA_WEB", "http://localhost:8501")
SAIDA = "/root/deva-continuo/figuras/png"
os.makedirs(SAIDA, exist_ok=True)

ABAS = [
    ("dc-tela-1-painel", "Painel"),
    ("dc-tela-2-memoria", "Memória"),
    ("dc-tela-3-propostas", "Propostas"),
    ("dc-tela-4-excecoes", "Exceções"),
]


async def principal():
    async with async_playwright() as p:
        navegador = await p.chromium.launch()
        pagina = await navegador.new_page(viewport={"width": 1500, "height": 1000},
                                          device_scale_factor=2)
        await pagina.goto(WEB, wait_until="networkidle")
        await pagina.wait_for_timeout(3500)

        # preenche o nome do auditor na barra lateral: sem ele os botões ficam inertes,
        # e a tela precisa aparecer no material do jeito que o aluno vai usar
        try:
            campo = pagina.locator('input[type="text"]').first
            await campo.fill("Camila Rocha")
            await campo.press("Enter")
            await pagina.wait_for_timeout(3000)
        except Exception as erro:
            print("não consegui preencher o auditor:", erro)

        for arquivo, aba in ABAS:
            try:
                await pagina.get_by_role("tab", name=aba).click()
                await pagina.wait_for_timeout(2200)
            except Exception as erro:
                print(f"não consegui abrir a aba {aba}:", erro)
            await pagina.screenshot(path=f"{SAIDA}/{arquivo}.png")
            print("ok", arquivo)

        await navegador.close()


asyncio.run(principal())
