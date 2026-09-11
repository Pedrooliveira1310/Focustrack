import flet as ft
import asyncio
import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path


# ============================================================
# CONFIGURAÇÕES
# ============================================================

APP_NAME = "FocusTrack"

BG = "#F3F0E8"
SURFACE = "#FFFDF8"
PRIMARY = "#173F35"
PRIMARY_DARK = "#0E2C25"
PRIMARY_LIGHT = "#E1E9E4"
ACCENT = "#C96B3C"
TEXT = "#171816"
MUTED = "#77756C"
BORDER = "#D9D5CA"
SUCCESS = "#39735A"
DANGER = "#A84235"


# ============================================================
# BANCO DE DADOS
# ============================================================

DB_PATH = Path(__file__).parent / "focustrack.db"


class Database:

    def __init__(self):
        self.conn = sqlite3.connect(
            DB_PATH,
            check_same_thread=False
        )

        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                materia TEXT NOT NULL,
                assunto TEXT NOT NULL,
                duracao INTEGER NOT NULL,
                data TEXT NOT NULL,
                criado_em TEXT NOT NULL
            )
        """)

        self.conn.commit()

    def add(self, materia, assunto, duracao, data_registro):
        self.conn.execute(
            """
            INSERT INTO sessions
            (materia, assunto, duracao, data, criado_em)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                materia,
                assunto,
                duracao,
                data_registro,
                datetime.now().isoformat()
            )
        )

        self.conn.commit()

    def update(
        self,
        session_id,
        materia,
        assunto,
        duracao,
        data_registro
    ):
        self.conn.execute(
            """
            UPDATE sessions
            SET materia = ?,
                assunto = ?,
                duracao = ?,
                data = ?
            WHERE id = ?
            """,
            (
                materia,
                assunto,
                duracao,
                data_registro,
                session_id
            )
        )

        self.conn.commit()

    def delete(self, session_id):
        self.conn.execute(
            "DELETE FROM sessions WHERE id = ?",
            (session_id,)
        )

        self.conn.commit()

    def all(self):
        cursor = self.conn.execute(
            """
            SELECT
                id,
                materia,
                assunto,
                duracao,
                data,
                criado_em
            FROM sessions
            ORDER BY data DESC, id DESC
            """
        )

        return cursor.fetchall()

    def materias(self):
        cursor = self.conn.execute(
            """
            SELECT DISTINCT materia
            FROM sessions
            ORDER BY materia
            """
        )

        return [row[0] for row in cursor.fetchall()]

    def close(self):
        self.conn.close()


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def format_minutes(minutes):

    minutes = int(minutes or 0)

    hours = minutes // 60
    mins = minutes % 60

    if hours > 0 and mins > 0:
        return f"{hours}h {mins}min"

    if hours > 0:
        return f"{hours}h"

    return f"{mins}min"


def format_date(value):

    try:
        d = datetime.strptime(value, "%Y-%m-%d")
        return d.strftime("%d/%m/%Y")

    except Exception:
        return value


def today_string():
    return date.today().strftime("%Y-%m-%d")


# ============================================================
# APLICAÇÃO
# ============================================================

def main(page: ft.Page):

    db = Database()

    # ========================================================
    # CONFIGURAÇÃO DA JANELA
    # ========================================================

    page.title = APP_NAME
    page.bgcolor = BG
    page.padding = 0

    page.window.width = 1180
    page.window.height = 780
    page.window.min_width = 850
    page.window.min_height = 600

    # ========================================================
    # ESTADO
    # ========================================================

    current_view = "dashboard"

    editing_id = None

    timer_total = 25 * 60
    timer_remaining = 25 * 60
    timer_running = False

    # ========================================================
    # COMPONENTES BÁSICOS
    # ========================================================

    def make_text(
        value,
        size=14,
        color=TEXT,
        weight=None
    ):

        return ft.Text(
            value,
            size=size,
            color=color,
            weight=weight
        )

    def field(label, hint=""):

        return ft.TextField(
            label=label,
            hint_text=hint,
            filled=True,
            fill_color=SURFACE,
            border_color=BORDER,
            focused_border_color=PRIMARY,
            border_radius=8
        )

    def show_message(message, color=PRIMARY):

        page.snack_bar = ft.SnackBar(
            content=make_text(
                message,
                color="#FFFFFF"
            ),
            bgcolor=color
        )

        page.snack_bar.open = True
        page.update()

    # ========================================================
    # CAMPOS
    # ========================================================

    materia_field = field(
        "Matéria",
        "Ex.: Matemática"
    )

    assunto_field = field(
        "Assunto",
        "Ex.: Funções"
    )

    duracao_field = field(
        "Duração",
        "Ex.: 50"
    )

    data_field = field(
        "Data",
        "AAAA-MM-DD"
    )

    data_field.value = today_string()

    # ========================================================
    # CRONÔMETRO
    # ========================================================

    timer_display = ft.Text(
        "25:00",
        size=64,
        color=TEXT,
        weight=ft.FontWeight.BOLD
    )

    timer_status = ft.Text(
        "SESSÃO DE FOCO",
        size=12,
        color=MUTED,
        weight=ft.FontWeight.BOLD
    )

    timer_progress = ft.ProgressBar(
        value=1,
        color=ACCENT,
        bgcolor=BORDER
    )

    timer_button = ft.ElevatedButton(
        "INICIAR",
        bgcolor=PRIMARY,
        color="#FFFFFF"
    )

    timer_minutes_field = ft.TextField(
        label="Minutos",
        value="25",
        width=130,
        filled=True,
        fill_color=SURFACE,
        border_color=BORDER,
        focused_border_color=PRIMARY,
        border_radius=8
    )

    def update_timer():

        minutes = timer_remaining // 60
        seconds = timer_remaining % 60

        timer_display.value = (
            f"{minutes:02d}:{seconds:02d}"
        )

        if timer_total > 0:
            timer_progress.value = (
                timer_remaining / timer_total
            )
        else:
            timer_progress.value = 0

    async def timer_loop():

        nonlocal timer_running
        nonlocal timer_remaining

        while timer_running and timer_remaining > 0:

            await asyncio.sleep(1)

            if not timer_running:
                break

            timer_remaining -= 1

            update_timer()

            page.update()

        if timer_remaining <= 0:

            timer_running = False

            timer_button.content = "INICIAR"
            timer_status.value = "SESSÃO CONCLUÍDA"

            show_message(
                "Sessão concluída!",
                SUCCESS
            )

            page.update()

    def start_timer(e):

        nonlocal timer_running

        if timer_running:

            timer_running = False

            timer_button.content = "CONTINUAR"
            timer_status.value = "SESSÃO PAUSADA"

            page.update()

            return

        timer_running = True

        timer_button.content = "PAUSAR"
        timer_status.value = "SESSÃO DE FOCO"

        page.run_task(timer_loop)

        page.update()

    def reset_timer(e):

        nonlocal timer_running
        nonlocal timer_total
        nonlocal timer_remaining

        timer_running = False

        try:

            minutes = int(
                timer_minutes_field.value
            )

            if minutes <= 0:
                raise ValueError

        except Exception:

            minutes = 25
            timer_minutes_field.value = "25"

        timer_total = minutes * 60
        timer_remaining = timer_total

        timer_button.content = "INICIAR"
        timer_status.value = "SESSÃO DE FOCO"

        update_timer()

        page.update()

    timer_button.on_click = start_timer

    # ========================================================
    # ÁREA DE CONTEÚDO
    # ========================================================

    content = ft.Column(
        expand=True,
        scroll=ft.ScrollMode.AUTO,
        spacing=20
    )

    page_title = ft.Text(
        "Visão geral",
        size=22,
        color=TEXT,
        weight=ft.FontWeight.BOLD
    )

    # ========================================================
    # DASHBOARD
    # ========================================================

    def build_dashboard():

        sessions = db.all()

        today = today_string()

        today_sessions = [
            s for s in sessions
            if s[4] == today
        ]

        today_minutes = sum(
            s[3] for s in today_sessions
        )

        total_minutes = sum(
            s[3] for s in sessions
        )

        # --------------------------------------------
        # ESTATÍSTICAS
        # --------------------------------------------

        stats = ft.Row(
            spacing=12,
            controls=[
                ft.Container(
                    expand=True,
                    bgcolor=SURFACE,
                    padding=20,
                    border_radius=8,
                    content=ft.Column(
                        spacing=5,
                        controls=[
                            make_text(
                                "HOJE",
                                11,
                                MUTED,
                                ft.FontWeight.BOLD
                            ),
                            make_text(
                                format_minutes(
                                    today_minutes
                                ),
                                28,
                                TEXT,
                                ft.FontWeight.BOLD
                            ),
                            make_text(
                                f"{len(today_sessions)} sessões",
                                12,
                                MUTED
                            )
                        ]
                    )
                ),

                ft.Container(
                    expand=True,
                    bgcolor=SURFACE,
                    padding=20,
                    border_radius=8,
                    content=ft.Column(
                        spacing=5,
                        controls=[
                            make_text(
                                "SESSÕES",
                                11,
                                MUTED,
                                ft.FontWeight.BOLD
                            ),
                            make_text(
                                str(len(sessions)),
                                28,
                                TEXT,
                                ft.FontWeight.BOLD
                            ),
                            make_text(
                                "registradas",
                                12,
                                MUTED
                            )
                        ]
                    )
                ),

                ft.Container(
                    expand=True,
                    bgcolor=SURFACE,
                    padding=20,
                    border_radius=8,
                    content=ft.Column(
                        spacing=5,
                        controls=[
                            make_text(
                                "TEMPO TOTAL",
                                11,
                                MUTED,
                                ft.FontWeight.BOLD
                            ),
                            make_text(
                                format_minutes(
                                    total_minutes
                                ),
                                28,
                                TEXT,
                                ft.FontWeight.BOLD
                            ),
                            make_text(
                                "tempo estudado",
                                12,
                                MUTED
                            )
                        ]
                    )
                )
            ]
        )

        # --------------------------------------------
        # TIMER
        # --------------------------------------------

        timer_panel = ft.Container(
            expand=True,
            bgcolor=SURFACE,
            padding=28,
            border_radius=8,
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=18,
                controls=[
                    make_text(
                        "CRONÔMETRO",
                        11,
                        MUTED,
                        ft.FontWeight.BOLD
                    ),

                    timer_status,

                    timer_display,

                    timer_progress,

                    ft.Row(
                        alignment=ft.MainAxisAlignment.CENTER,
                        controls=[
                            timer_button,

                            ft.TextButton(
                                "REINICIAR",
                                on_click=reset_timer
                            ),

                            timer_minutes_field
                        ]
                    )
                ]
            )
        )

        # --------------------------------------------
        # MATÉRIAS
        # --------------------------------------------

        totals = {}

        for session in sessions:

            materia = session[1]
            duracao = session[3]

            if materia not in totals:
                totals[materia] = 0

            totals[materia] += duracao

        subject_controls = [
            make_text(
                "TEMPO POR MATÉRIA",
                11,
                MUTED,
                ft.FontWeight.BOLD
            )
        ]

        ordered = sorted(
            totals.items(),
            key=lambda x: x[1],
            reverse=True
        )

        if not ordered:

            subject_controls.append(
                make_text(
                    "Nenhuma sessão registrada.",
                    13,
                    MUTED
                )
            )

        else:

            for materia, minutos in ordered[:6]:

                subject_controls.append(
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            make_text(
                                materia,
                                13,
                                TEXT
                            ),
                            make_text(
                                format_minutes(minutos),
                                13,
                                TEXT,
                                ft.FontWeight.BOLD
                            )
                        ]
                    )
                )

        subject_panel = ft.Container(
            width=320,
            bgcolor=SURFACE,
            padding=24,
            border_radius=8,
            content=ft.Column(
                spacing=15,
                controls=subject_controls
            )
        )

        # --------------------------------------------
        # SESSÕES RECENTES
        # --------------------------------------------

        recent_controls = [
            make_text(
                "SESSÕES RECENTES",
                11,
                MUTED,
                ft.FontWeight.BOLD
            )
        ]

        if not sessions:

            recent_controls.append(
                make_text(
                    "Nenhuma sessão registrada.",
                    13,
                    MUTED
                )
            )

        else:

            for session in sessions[:5]:

                materia = session[1]
                assunto = session[2]
                duracao = session[3]
                data_registro = session[4]

                recent_controls.append(
                    ft.Container(
                        padding=12,
                        bgcolor=BG,
                        border_radius=6,
                        content=ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            controls=[
                                ft.Column(
                                    expand=True,
                                    spacing=3,
                                    controls=[
                                        make_text(
                                            materia,
                                            14,
                                            TEXT,
                                            ft.FontWeight.BOLD
                                        ),
                                        make_text(
                                            assunto,
                                            12,
                                            MUTED
                                        )
                                    ]
                                ),

                                ft.Column(
                                    horizontal_alignment=(
                                        ft.CrossAxisAlignment.END
                                    ),
                                    spacing=3,
                                    controls=[
                                        make_text(
                                            format_minutes(
                                                duracao
                                            ),
                                            13,
                                            TEXT,
                                            ft.FontWeight.BOLD
                                        ),
                                        make_text(
                                            format_date(
                                                data_registro
                                            ),
                                            11,
                                            MUTED
                                        )
                                    ]
                                )
                            ]
                        )
                    )
                )

        recent_panel = ft.Container(
            bgcolor=SURFACE,
            padding=24,
            border_radius=8,
            content=ft.Column(
                spacing=10,
                controls=recent_controls
            )
        )

        # --------------------------------------------
        # CONTEÚDO
        # --------------------------------------------

        content.controls.clear()

        content.controls.extend([
            ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Column(
                        spacing=3,
                        controls=[
                            make_text(
                                "BOM ESTUDO.",
                                30,
                                TEXT,
                                ft.FontWeight.BOLD
                            ),
                            make_text(
                                "Organize seu estudo e acompanhe sua evolução.",
                                13,
                                MUTED
                            )
                        ]
                    ),

                    make_text(
                        date.today().strftime("%d/%m/%Y"),
                        13,
                        MUTED
                    )
                ]
            ),

            stats,

            ft.Row(
                vertical_alignment=(
                    ft.CrossAxisAlignment.START
                ),
                spacing=15,
                controls=[
                    timer_panel,
                    subject_panel
                ]
            ),

            recent_panel
        ])

    # ========================================================
    # SESSÕES
    # ========================================================

    search_field = ft.TextField(
        hint_text="Buscar...",
        filled=True,
        fill_color=SURFACE,
        border_color=BORDER,
        focused_border_color=PRIMARY,
        border_radius=8,
        expand=True
    )

    subject_filter = ft.Dropdown(
        label="Matéria",
        value="Todas",
        width=180,
        options=[
            ft.DropdownOption(
                key="Todas",
                text="Todas"
            )
        ]
    )

    period_filter = ft.Dropdown(
        label="Período",
        value="Todos",
        width=170,
        options=[
            ft.DropdownOption(
                key="Todos",
                text="Todos"
            ),
            ft.DropdownOption(
                key="Hoje",
                text="Hoje"
            ),
            ft.DropdownOption(
                key="7",
                text="7 dias"
            ),
            ft.DropdownOption(
                key="30",
                text="30 dias"
            )
        ]
    )

    sessions_list = ft.Column(
        spacing=10,
        expand=True
    )

    def update_subject_filter():

        options = [
            ft.DropdownOption(
                key="Todas",
                text="Todas"
            )
        ]

        for materia in db.materias():

            options.append(
                ft.DropdownOption(
                    key=materia,
                    text=materia
                )
            )

        subject_filter.options = options

    def delete_session(session_id):

        db.delete(session_id)

        update_subject_filter()
        build_sessions()
        build_dashboard()

        show_message(
            "Sessão excluída.",
            DANGER
        )

    def edit_session(session):

        nonlocal editing_id

        editing_id = session[0]

        materia_field.value = session[1]
        assunto_field.value = session[2]
        duracao_field.value = str(session[3])
        data_field.value = session[4]

        navigate("form")

    def build_session_card(session):

        session_id = session[0]
        materia = session[1]
        assunto = session[2]
        duracao = session[3]
        data_registro = session[4]

        return ft.Container(
            bgcolor=SURFACE,
            padding=18,
            border_radius=8,
            content=ft.Row(
                vertical_alignment=(
                    ft.CrossAxisAlignment.CENTER
                ),
                controls=[

                    ft.Container(
                        width=5,
                        height=55,
                        bgcolor=ACCENT
                    ),

                    ft.Column(
                        expand=True,
                        spacing=4,
                        controls=[
                            make_text(
                                materia,
                                16,
                                TEXT,
                                ft.FontWeight.BOLD
                            ),
                            make_text(
                                assunto,
                                13,
                                MUTED
                            )
                        ]
                    ),

                    ft.Column(
                        horizontal_alignment=(
                            ft.CrossAxisAlignment.END
                        ),
                        spacing=3,
                        controls=[
                            make_text(
                                format_minutes(
                                    duracao
                                ),
                                13,
                                TEXT,
                                ft.FontWeight.BOLD
                            ),
                            make_text(
                                format_date(
                                    data_registro
                                ),
                                11,
                                MUTED
                            )
                        ]
                    ),

                    ft.TextButton(
                        "EDITAR",
                        on_click=lambda e, s=session:
                        edit_session(s)
                    ),

                    ft.TextButton(
                        "EXCLUIR",
                        style=ft.ButtonStyle(
                            color=DANGER
                        ),
                        on_click=lambda e, sid=session_id:
                        delete_session(sid)
                    )
                ]
            )
        )

    def build_sessions(e=None):

        sessions_list.controls.clear()

        query = (
            search_field.value or ""
        ).lower().strip()

        selected_subject = (
            subject_filter.value or "Todas"
        )

        selected_period = (
            period_filter.value or "Todos"
        )

        today = date.today()

        sessions = db.all()

        filtered = []

        for session in sessions:

            materia = session[1]
            assunto = session[2]
            data_registro = session[4]

            # Busca
            if query:

                if (
                    query not in materia.lower()
                    and query not in assunto.lower()
                ):
                    continue

            # Matéria
            if (
                selected_subject != "Todas"
                and materia != selected_subject
            ):
                continue

            # Período
            if selected_period != "Todos":

                try:

                    session_date = datetime.strptime(
                        data_registro,
                        "%Y-%m-%d"
                    ).date()

                except Exception:
                    continue

                if selected_period == "Hoje":

                    if session_date != today:
                        continue

                elif selected_period == "7":

                    if session_date < (
                        today - timedelta(days=6)
                    ):
                        continue

                elif selected_period == "30":

                    if session_date < (
                        today - timedelta(days=29)
                    ):
                        continue

            filtered.append(session)

        if not filtered:

            sessions_list.controls.append(
                ft.Container(
                    bgcolor=SURFACE,
                    padding=30,
                    border_radius=8,
                    content=ft.Column(
                        horizontal_alignment=(
                            ft.CrossAxisAlignment.CENTER
                        ),
                        controls=[
                            make_text(
                                "Nenhuma sessão encontrada.",
                                16,
                                TEXT,
                                ft.FontWeight.BOLD
                            ),
                            make_text(
                                "Tente alterar os filtros.",
                                13,
                                MUTED
                            )
                        ]
                    )
                )
            )

        else:

            for session in filtered:

                sessions_list.controls.append(
                    build_session_card(session)
                )

        page.update()

    search_field.on_change = build_sessions
    subject_filter.on_change = build_sessions
    period_filter.on_change = build_sessions

    # ========================================================
    # FORMULÁRIO
    # ========================================================

    form_title = ft.Text(
        "NOVA SESSÃO",
        size=28,
        color=TEXT,
        weight=ft.FontWeight.BOLD
    )

    def clear_form():

        nonlocal editing_id

        editing_id = None

        materia_field.value = ""
        assunto_field.value = ""
        duracao_field.value = ""
        data_field.value = today_string()

        form_title.value = "NOVA SESSÃO"

        page.update()

    def save_session(e):

        nonlocal editing_id

        materia = (
            materia_field.value or ""
        ).strip()

        assunto = (
            assunto_field.value or ""
        ).strip()

        duracao = (
            duracao_field.value or ""
        ).strip()

        data_registro = (
            data_field.value or ""
        ).strip()

        if not materia:

            show_message(
                "Digite a matéria.",
                DANGER
            )

            return

        if not assunto:

            show_message(
                "Digite o assunto.",
                DANGER
            )

            return

        try:

            duracao_int = int(duracao)

            if duracao_int <= 0:
                raise ValueError

        except Exception:

            show_message(
                "A duração deve ser um número.",
                DANGER
            )

            return

        try:

            datetime.strptime(
                data_registro,
                "%Y-%m-%d"
            )

        except Exception:

            show_message(
                "Use a data no formato AAAA-MM-DD.",
                DANGER
            )

            return

        if editing_id is None:

            db.add(
                materia,
                assunto,
                duracao_int,
                data_registro
            )

            message = "Sessão registrada."

        else:

            db.update(
                editing_id,
                materia,
                assunto,
                duracao_int,
                data_registro
            )

            message = "Sessão atualizada."

        clear_form()

        update_subject_filter()
        build_dashboard()
        build_sessions()

        navigate("dashboard")

        show_message(
            message,
            SUCCESS
        )

    def build_form():

        return ft.Column(
            expand=True,
            scroll=ft.ScrollMode.AUTO,
            spacing=20,
            controls=[

                ft.Column(
                    spacing=5,
                    controls=[
                        make_text(
                            "REGISTRO",
                            11,
                            MUTED,
                            ft.FontWeight.BOLD
                        ),

                        form_title,

                        make_text(
                            "Registre uma sessão de estudo.",
                            13,
                            MUTED
                        )
                    ]
                ),

                ft.Container(
                    bgcolor=SURFACE,
                    padding=28,
                    border_radius=8,
                    content=ft.Column(
                        spacing=18,
                        controls=[

                            materia_field,

                            assunto_field,

                            duracao_field,

                            data_field,

                            ft.Row(
                                alignment=(
                                    ft.MainAxisAlignment.END
                                ),
                                controls=[

                                    ft.TextButton(
                                        "LIMPAR",
                                        on_click=lambda e:
                                        clear_form()
                                    ),

                                    ft.ElevatedButton(
                                        "SALVAR",
                                        bgcolor=PRIMARY,
                                        color="#FFFFFF",
                                        on_click=save_session
                                    )
                                ]
                            )
                        ]
                    )
                )
            ]
        )

    # ========================================================
    # SIDEBAR
    # ========================================================

    def sidebar_button(label, view):

        return ft.TextButton(
            label,
            style=ft.ButtonStyle(
                color="#FFFFFF"
            ),
            on_click=lambda e: navigate(view)
        )

    sidebar = ft.Container(
        width=230,
        bgcolor=PRIMARY,
        padding=20,
        content=ft.Column(
            spacing=10,
            controls=[

                ft.Container(
                    padding=10,
                    content=ft.Column(
                        spacing=0,
                        controls=[
                            make_text(
                                "FOCUS",
                                27,
                                "#FFFFFF",
                                ft.FontWeight.BOLD
                            ),

                            make_text(
                                "TRACK",
                                14,
                                "#BFD1C9",
                                ft.FontWeight.BOLD
                            ),

                            make_text(
                                "Estude com intenção.",
                                11,
                                "#AFC4BB"
                            )
                        ]
                    )
                ),

                ft.Container(
                    height=15
                ),

                make_text(
                    "NAVEGAÇÃO",
                    10,
                    "#8FA99F",
                    ft.FontWeight.BOLD
                ),

                sidebar_button(
                    "VISÃO GERAL",
                    "dashboard"
                ),

                sidebar_button(
                    "SESSÕES",
                    "sessions"
                ),

                sidebar_button(
                    "NOVA SESSÃO",
                    "form"
                ),

                ft.Container(
                    expand=True
                ),

                ft.Container(
                    padding=10,
                    content=ft.Column(
                        spacing=5,
                        controls=[
                            make_text(
                                "DISCIPLINA > MOTIVAÇÃO",
                                10,
                                "#8FA99F",
                                ft.FontWeight.BOLD
                            ),

                            make_text(
                                "Pequenos blocos de foco,\nconsistentemente.",
                                12,
                                "#D9E4DF"
                            )
                        ]
                    )
                )
            ]
        )
    )

    # ========================================================
    # HEADER
    # ========================================================

    header = ft.Container(
        height=70,
        padding=20,
        bgcolor=BG,
        content=ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                page_title,

                make_text(
                    "FOCUS / TRACK",
                    11,
                    MUTED,
                    ft.FontWeight.BOLD
                )
            ]
        )
    )

    # ========================================================
    # NAVEGAR
    # ========================================================

    def navigate(view):

        nonlocal current_view

        current_view = view

        if view == "dashboard":

            page_title.value = "Visão geral"

            build_dashboard()

        elif view == "sessions":

            page_title.value = "Sessões"

            update_subject_filter()
            build_sessions()

            content.controls.clear()

            content.controls.extend([
                ft.Row(
                    spacing=10,
                    controls=[
                        search_field,
                        subject_filter,
                        period_filter
                    ]
                ),

                sessions_list
            ])

        elif view == "form":

            if editing_id is None:
                form_title.value = "NOVA SESSÃO"
            else:
                form_title.value = "EDITAR SESSÃO"

            page_title.value = (
                "Nova sessão"
                if editing_id is None
                else "Editar sessão"
            )

            content.controls.clear()

            content.controls.append(
                build_form()
            )

        page.update()

    # ========================================================
    # LAYOUT PRINCIPAL
    # ========================================================

    main_column = ft.Column(
        expand=True,
        spacing=0,
        controls=[
            header,

            ft.Container(
                expand=True,
                padding=25,
                content=content
            )
        ]
    )

    layout = ft.Row(
        expand=True,
        spacing=0,
        controls=[
            sidebar,
            main_column
        ]
    )

    # ========================================================
    # INICIALIZAÇÃO
    # ========================================================

    update_timer()

    build_dashboard()

    page.add(layout)

    page.update()


# ============================================================
# EXECUTAR
# ============================================================

if __name__ == "__main__":
    ft.run(main)