import flet as ft
import asyncio


def main(page: ft.Page):
    page.title = "FocusTrack"
    page.bgcolor = "#F5F5F5"
    page.window.width = 320
    page.window.height = 600
    page.padding = 20
    page.scroll = ft.ScrollMode.AUTO

    titulo = ft.Text(
        "FocusTrack 🎯",
        size=30,
        weight=ft.FontWeight.BOLD
    )

    subtitulo = ft.Text(
        "Organize seus estudos",
        size=16
    )

    timer = ft.Text(
        "25:00",
        size=40,
        weight=ft.FontWeight.BOLD
    )

    segundos = 25 * 60
    timer_rodando = False

    async def iniciar_timer(e):
        nonlocal segundos, timer_rodando

        if timer_rodando:
            return

        timer_rodando = True

        while segundos > 0 and timer_rodando:
            await asyncio.sleep(1)

            segundos -= 1

            minutos = segundos // 60
            segundos_restantes = segundos % 60

            timer.value = f"{minutos:02d}:{segundos_restantes:02d}"

            page.update()

        if segundos == 0:
            timer.value = "Tempo esgotado!"
            timer_rodando = False
            page.update()

    def parar_timer(e):
        nonlocal timer_rodando

        timer_rodando = False

    def resetar_timer(e):
        nonlocal segundos, timer_rodando

        timer_rodando = False
        segundos = 25 * 60
        timer.value = "25:00"

        page.update()

    iniciar_button = ft.IconButton(
        icon=ft.Icons.PLAY_ARROW,
        icon_size=40,
        icon_color=ft.Colors.GREEN,
        width=300,
        on_click=lambda e: page.run_task(iniciar_timer, e)
    )

    parar_button = ft.IconButton(
        icon=ft.Icons.STOP,
        icon_size=40,
        icon_color=ft.Colors.RED,
        width=300,
        on_click=parar_timer
    )

    resetar_button = ft.IconButton(
        icon=ft.Icons.REFRESH,
        icon_size=40,
        icon_color=ft.Colors.BLUE,
        width=300,
        on_click=resetar_timer
    )

    materia = ft.TextField(
        label="Matéria",
        width=300,
    )

    assunto = ft.TextField(
        label="Assunto",
        width=300,
    )

    tempo = ft.TextField(
        label="Tempo (minutos)",
        width=300,
    )

    lista_sessoes = ft.Column()

    quantidade_sessoes = ft.Text(
        "Sessões de estudo:",
        size=16,
        weight=ft.FontWeight.BOLD
    )

    def adicionar_sessao(e):
        materia_value = materia.value
        assunto_value = assunto.value
        tempo_value = tempo.value

        def excluir_sessao(e):
            lista_sessoes.controls.remove(sessao)

            quantidade_sessoes.value = (
                f"Sessões de estudo: {len(lista_sessoes.controls)}"
            )

            page.update()

        sessao = ft.Container(
            ft.Row(
                [
                    ft.Column(
                        [
                            ft.Text(f"📚 {materia_value}"),
                            ft.Text(f"{assunto_value}"),
                            ft.Text(f"⏱️ {tempo_value} minutos")
                        ]
                    ),

                    ft.IconButton(
                        icon=ft.Icons.DELETE,
                        icon_color=ft.Colors.RED,
                        on_click=excluir_sessao
                    )
                ]
            ),
            padding=10,
            bgcolor="#E0E0E0",
            border_radius=5
        )

        lista_sessoes.controls.append(sessao)

        materia.value = ""
        assunto.value = ""
        tempo.value = ""

        quantidade_sessoes.value = (
            f"Sessões de estudo: {len(lista_sessoes.controls)}"
        )

        page.update()

    adicionar_button = ft.ElevatedButton(
        content=ft.Text("Adicionar sessão de estudo"),
        width=300,
        on_click=adicionar_sessao
    )

    pagina = ft.Column(
        controls=[
            titulo,
            subtitulo,
            timer,
            iniciar_button,
            parar_button,
            resetar_button,
            materia,
            assunto,
            tempo,
            adicionar_button,
            quantidade_sessoes,
            lista_sessoes
        ],
        scroll=ft.ScrollMode.AUTO
    )

    page.add(pagina)


ft.app(target=main)