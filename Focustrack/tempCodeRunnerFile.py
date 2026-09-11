import flet as ft
import asyncio
import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path

# ============================================================
# FocusTrack — estudo, foco e produtividade
# Redesign visual completo
# ============================================================

APP_NAME = "FocusTrack"

# ------------------------------------------------------------
# IDENTIDADE VISUAL
# ------------------------------------------------------------

BG = "#F3F0E8"              # papel / creme
SURFACE = "#FFFDF8"         # branco quente
SURFACE_DARK = "#173F35"    # verde garrafa
TEXT = "#171816"            # quase preto
MUTED = "#77756C"           # cinza quente
BORDER = "#D9D5CA"

PRIMARY = "#173F35"         # verde principal
PRIMARY_DARK = "#0E2C25"
PRIMARY_LIGHT = "#E1E9E4"

ACCENT = "#C96B3C"          # terracota
ACCENT_LIGHT = "#F3DED3"

SUCCESS = "#39735A"
WARNING = "#B98232"
DANGER = "#A84235"

DB_PATH = Path(__file__).resolve().parent / "focustrack.db"


# ============================================================
# BANCO DE DADOS
# ============================================================

class Database:
    def __init__(self, path=DB_PATH):
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row

        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                materia TEXT NOT NULL,
                assunto TEXT,
                duracao INTEGER NOT NULL CHECK(duracao > 0),
                data TEXT NOT NULL,
                criado_em TEXT NOT NULL
            )
            """
        )

        self.conn.commit()

    def add(self, materia, assunto, duracao, data_sessao):
        cur = self.conn.execute(
            """
            INSERT INTO sessions
            (materia, assunto, duracao, data, criado_em)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                materia.strip(),
                assunto.strip(),
                int(duracao),
                data_sessao,
                datetime.now().isoformat(timespec="seconds"),
            ),
        )

        self.conn.commit()
        return cur.lastrowid

    def update(self, session_id, materia, assunto, duracao, data_sessao):
        self.conn.execute(
            """
            UPDATE sessions
            SET materia=?, assunto=?, duracao=?, data=?
            WHERE id=?
            """,
            (
                materia.strip(),
                assunto.strip(),
                int(duracao),
                data_sessao,
                session_id,
            ),
        )

        self.conn.commit()

    def delete(self, session_id):
        self.conn.execute(
            "DELETE FROM sessions WHERE id=?",
            (session_id,),
        )

        self.conn.commit()

    def all(self, search="", materia="Todas", period="Todos"):
        query = "SELECT * FROM sessions WHERE 1=1"
        params = []

        if materia and materia != "Todas":
            query += " AND materia = ?"
            params.append(materia)

        if search.strip():
            query += " AND (materia LIKE ? OR assunto LIKE ?)"
            value = f"%{search.strip()}%"
            params.extend([value, value])

        if period == "Hoje":
            query += " AND data = ?"
            params.append(date.today().isoformat())

        elif period == "7 dias":
            query += " AND data >= ?"
            params.append(
                (date.today() - timedelta(days=6)).isoformat()
            )

        elif period == "30 dias":
            query += " AND data >= ?"
            params.append(
                (date.today() - timedelta(days=29)).isoformat()
            )

        query += " ORDER BY data DESC, id DESC"

        return self.conn.execute(query, params).fetchall()

    def materias(self):
        rows = self.conn.execute(
            """
            SELECT DISTINCT materia
            FROM sessions
            ORDER BY materia COLLATE NOCASE
            """
        ).fetchall()

        return [r["materia"] for r in rows]

    def stats(self):
        row = self.conn.execute(
            """
            SELECT
                COUNT(*) total,
                COALESCE(SUM(duracao),0) minutos
            FROM sessions
            """
        ).fetchone()

        today = date.today().isoformat()

        today_row = self.conn.execute(
            """
            SELECT
                COUNT(*) total,
                COALESCE(SUM(duracao),0) minutos
            FROM sessions
            WHERE data=?
            """,
            (today,),
        ).fetchone()

        week_row = self.conn.execute(
            """
            SELECT
                COUNT(*) total,
                COALESCE(SUM(duracao),0) minutos
            FROM sessions
            WHERE data>=?
            """,
            (
                (date.today() - timedelta(days=6)).isoformat(),
            ),
        ).fetchone()

        top = self.conn.execute(
            """
            SELECT materia, SUM(duracao) total
            FROM sessions
            GROUP BY materia
            ORDER BY total DESC
            LIMIT 5
            """
        ).fetchall()

        return {
            "total": row["total"],
            "minutos": row["minutos"],
            "hoje": today_row["total"],
            "minutos_hoje": today_row["minutos"],
            "minutos_semana": week_row["minutos"],
            "top": [
                (r["materia"], r["total"])
                for r in top
            ],
        }

    def close(self):
        self.conn.close()


# ============================================================
# HELPERS
# ============================================================

def format_minutes(minutes):
    hours, mins = divmod(int(minutes), 60)

    if hours and mins:
        return f"{hours}h {mins}min"

    if hours:
        return f"{hours}h"

    return f"{mins}min"


def format_date(value):
    try:
        return datetime.strptime(
            value,
            "%Y-%m-%d"
        ).strftime("%d/%m/%Y")

    except ValueError:
        return value


def format_date_long(value):
    try:
        d = datetime.strptime(value, "%Y-%m-%d")
        return d.strftime("%d %b").upper()

    except ValueError:
        return value


# ============================================================
# APP
# ============================================================

def main(page: ft.Page):

    db = Database()

    # --------------------------------------------------------
    # CONFIGURAÇÃO
    # --------------------------------------------------------

    page.title = APP_NAME
    page.bgcolor = BG
    page.padding = 0
    page.theme_mode = ft.ThemeMode.LIGHT

    page.theme = ft.Theme(
        color_scheme_seed=PRIMARY,
        use_material3=True,
        font_family="Inter",
    )

    page.window.width = 1180
    page.window.height = 780
    page.window.min_width = 850
    page.window.min_height = 620

    current_view = "dashboard"
    editing_id = None

    timer_seconds = 25 * 60
    timer_running = False
    timer_initial = 25 * 60

    # ========================================================
    # ESTILO DOS CAMPOS
    # ========================================================

    def field_style():
        return ft.InputDecorationTheme(
            filled=True,
            fill_color=SURFACE,
            border=ft.OutlineInputBorder(
                border_radius=8,
                border_side=ft.BorderSide(
                    1,
                    BORDER,
                ),
            ),
            focused_border=ft.OutlineInputBorder(
                border_radius=8,
                border_side=ft.BorderSide(
                    1.5,
                    PRIMARY,
                ),
            ),
            label_style=ft.TextStyle(
                color=MUTED,
            ),
        )

    page.theme.input_decoration_theme = field_style()

    # ========================================================
    # NOTIFICAÇÃO
    # ========================================================

    def snack(message, color=TEXT):

        page.snack_bar = ft.SnackBar(
            content=ft.Text(
                message,
                color=ft.Colors.WHITE,
            ),
            bgcolor=color,
            behavior=ft.SnackBarBehavior.FLOATING,
        )

        page.snack_bar.open = True
        page.update()

    # ========================================================
    # COMPONENTES VISUAIS
    # ========================================================

    def divider():
        return ft.Container(
            height=1,
            bgcolor=BORDER,
        )

    def section_label(text):
        return ft.Text(
            text.upper(),
            size=11,
            weight=ft.FontWeight.BOLD,
            color=MUTED,
            letter_spacing=1.2,
        )

    def page_title(title, subtitle=None):

        controls = [
            ft.Text(
                title,
                size=32,
                weight=ft.FontWeight.BOLD,
                color=TEXT,
            )
        ]

        if subtitle:
            controls.append(
                ft.Text(
                    subtitle,
                    size=14,
                    color=MUTED,
                )
            )

        return ft.Column(
            controls,
            spacing=5,
        )

    def simple_container(content, padding=22):

        return ft.Container(
            content=content,
            bgcolor=SURFACE,
            border=ft.Border.all(
                1,
                BORDER,
            ),
            border_radius=10,
            padding=padding,
        )

    # ========================================================
    # TIMER
    # ========================================================

    timer_text = ft.Text(
        "25:00",
        size=68,
        weight=ft.FontWeight.BOLD,
        color=TEXT,
        font_family="Inter",
    )

    timer_mode_text = ft.Text(
        "FOCO",
        size=11,
        weight=ft.FontWeight.BOLD,
        color=PRIMARY,
        letter_spacing=2,
    )

    timer_progress = ft.ProgressBar(
        value=1,
        color=PRIMARY,
        bgcolor=PRIMARY_LIGHT,
        height=5,
    )

    focus_minutes = ft.Dropdown(
        width=145,
        value="25",
        options=[
            ft.DropdownOption(
                key="15",
                text="15 minutos",
            ),
            ft.DropdownOption(
                key="25",
                text="25 minutos",
            ),
            ft.DropdownOption(
                key="45",
                text="45 minutos",
            ),
            ft.DropdownOption(
                key="50",
                text="50 minutos",
            ),
            ft.DropdownOption(
                key="60",
                text="60 minutos",
            ),
        ],
    )

    def set_timer(e=None):

        nonlocal timer_seconds
        nonlocal timer_running
        nonlocal timer_initial

        try:
            minutes = int(
                focus_minutes.value
            )

        except (TypeError, ValueError):
            minutes = 25

        timer_running = False
        timer_seconds = minutes * 60
        timer_initial = timer_seconds

        timer_text.value = f"{minutes:02d}:00"
        timer_mode_text.value = "FOCO"
        timer_progress.value = 1

        page.update()

    def stop_timer(e):

        nonlocal timer_running

        timer_running = False

        snack(
            "Timer pausado.",
            MUTED,
        )

    async def run_timer(e=None):

        nonlocal timer_seconds
        nonlocal timer_running
        nonlocal timer_initial

        if timer_running:
            return

        timer_running = True

        if timer_seconds <= 0:
            timer_seconds = 25 * 60

        timer_initial = timer_seconds

        while timer_seconds > 0 and timer_running:

            await asyncio.sleep(1)

            if not timer_running:
                break

            timer_seconds -= 1

            mins, secs = divmod(
                timer_seconds,
                60,
            )

            timer_text.value = (
                f"{mins:02d}:{secs:02d}"
            )

            timer_progress.value = (
                timer_seconds / timer_initial
            )

            page.update()

        if timer_seconds == 0:

            timer_running = False

            timer_text.value = "00:00"
            timer_progress.value = 0

            page.update()

            snack(
                "Sessão concluída.",
                SUCCESS,
            )

    def timer_panel():

        return ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Column(
                                [
                                    section_label(
                                        "Sessão atual"
                                    ),
                                    ft.Container(
                                        height=5
                                    ),
                                    timer_mode_text,
                                ],
                                spacing=0,
                            ),
                            ft.Container(
                                expand=True
                            ),
                            focus_minutes,
                        ],
                        vertical_alignment=(
                            ft.CrossAxisAlignment.CENTER
                        ),
                    ),

                    ft.Container(
                        content=timer_text,
                        alignment=ft.Alignment(
                            0,
                            0,
                        ),
                        padding=ft.Padding(
                            0,
                            25,
                            0,
                            20,
                        ),
                    ),

                    timer_progress,

                    ft.Container(
                        height=12
                    ),

                    ft.Row(
                        [
                            ft.FilledButton(
                                "Iniciar",
                                icon=ft.Icons.PLAY_ARROW,
                                style=ft.ButtonStyle(
                                    bgcolor=PRIMARY,
                                    color=ft.Colors.WHITE,
                                    shape=ft.RoundedRectangleBorder(
                                        radius=7
                                    ),
                                ),
                                on_click=lambda e:
                                    page.run_task(
                                        run_timer,
                                        e,
                                    ),
                            ),

                            ft.OutlinedButton(
                                "Pausar",
                                icon=ft.Icons.PAUSE,
                                style=ft.ButtonStyle(
                                    shape=ft.RoundedRectangleBorder(
                                        radius=7
                                    ),
                                ),
                                on_click=stop_timer,
                            ),

                            ft.IconButton(
                                icon=ft.Icons.RESTART,
                                icon_color=MUTED,
                                tooltip="Reiniciar",
                                on_click=set_timer,
                            ),
                        ],
                        spacing=8,
                    ),
                ],
                spacing=0,
            ),
            bgcolor=SURFACE,
            border=ft.Border.all(
                1,
                BORDER,
            ),
            border_radius=10,
            padding=25,
        )

    # ========================================================
    # FORMULÁRIO
    # ========================================================

    materia_field = ft.TextField(
        label="Matéria",
    )

    assunto_field = ft.TextField(
        label="Assunto",
    )

    duracao_field = ft.TextField(
        label="Duração em minutos",
        keyboard_type=ft.KeyboardType.NUMBER,
    )

    data_field = ft.TextField(
        label="Data",
        value=date.today().isoformat(),
    )

    session_form_title = ft.Text(
        "Nova sessão",
        size=26,
        weight=ft.FontWeight.BOLD,
        color=TEXT,
    )

    def clear_form():

        nonlocal editing_id

        editing_id = None

        session_form_title.value = (
            "Nova sessão"
        )

        materia_field.value = ""
        assunto_field.value = ""
        duracao_field.value = ""
        data_field.value = date.today().isoformat()

    def validate_form():

        materia = (
            materia_field.value or ""
        ).strip()

        assunto = (
            assunto_field.value or ""
        ).strip()

        duracao = (
            duracao_field.value or ""
        ).strip()

        data_sessao = (
            data_field.value or ""
        ).strip()

        if not materia:

            snack(
                "Informe a matéria.",
                DANGER,
            )

            return None

        try:

            minutos = int(duracao)

            if minutos <= 0 or minutos > 1440:
                raise ValueError

        except ValueError:

            snack(
                "A duração deve estar entre 1 e 1440 minutos.",
                DANGER,
            )

            return None

        try:

            datetime.strptime(
                data_sessao,
                "%Y-%m-%d",
            )

        except ValueError:

            snack(
                "Use o formato AAAA-MM-DD.",
                DANGER,
            )

            return None

        return (
            materia,
            assunto,
            minutos,
            data_sessao,
        )

    def save_session(e):

        nonlocal editing_id

        data = validate_form()

        if not data:
            return

        (
            materia,
            assunto,
            minutos,
            data_sessao,
        ) = data

        if editing_id is None:

            db.add(
                materia,
                assunto,
                minutos,
                data_sessao,
            )

            snack(
                "Sessão registrada.",
                SUCCESS,
            )

        else:

            db.update(
                editing_id,
                materia,
                assunto,
                minutos,
                data_sessao,
            )

            snack(
                "Sessão atualizada.",
                PRIMARY,
            )

        clear_form()
        render()

    def edit_session(session_id):

        nonlocal editing_id

        row = db.conn.execute(
            "SELECT * FROM sessions WHERE id=?",
            (session_id,),
        ).fetchone()

        if not row:
            return

        editing_id = session_id

        session_form_title.value = (
            "Editar sessão"
        )

        materia_field.value = row["materia"]
        assunto_field.value = (
            row["assunto"] or ""
        )

        duracao_field.value = str(
            row["duracao"]
        )

        data_field.value = row["data"]

        current_view_set("form")

    # ========================================================
    # DELETE
    # ========================================================

    def confirm_delete(session_id):

        def close_dialog(e):

            dialog.open = False
            page.update()

        def delete(e):

            db.delete(session_id)

            dialog.open = False

            snack(
                "Sessão excluída.",
                DANGER,
            )

            render()

        dialog = ft.AlertDialog(
            modal=True,

            title=ft.Text(
                "Excluir sessão?"
            ),

            content=ft.Text(
                "Essa ação não pode ser desfeita."
            ),

            actions=[
                ft.TextButton(
                    "Cancelar",
                    on_click=close_dialog,
                ),

                ft.FilledButton(
                    "Excluir",
                    style=ft.ButtonStyle(
                        bgcolor=DANGER,
                        color=ft.Colors.WHITE,
                    ),
                    on_click=delete,
                ),
            ],
        )

        page.overlay.append(dialog)

        dialog.open = True

        page.update()

    # ========================================================
    # ITEM DE SESSÃO
    # ========================================================

    def session_row(row):

        return ft.Container(
            content=ft.Row(
                [
                    ft.Container(
                        width=8,
                        height=42,
                        bgcolor=ACCENT,
                        border_radius=2,
                    ),

                    ft.Container(
                        width=12
                    ),

                    ft.Column(
                        [
                            ft.Text(
                                row["materia"],
                                size=15,
                                weight=ft.FontWeight.BOLD,
                                color=TEXT,
                            ),

                            ft.Text(
                                row["assunto"]
                                or "Sem assunto",
                                size=12,
                                color=MUTED,
                            ),
                        ],
                        spacing=3,
                        expand=True,
                    ),

                    ft.Text(
                        format_minutes(
                            row["duracao"]
                        ),
                        size=13,
                        weight=ft.FontWeight.BOLD,
                        color=TEXT,
                    ),

                    ft.Text(
                        format_date_long(
                            row["data"]
                        ),
                        size=11,
                        color=MUTED,
                        width=65,
                        text_align=ft.TextAlign.RIGHT,
                    ),

                    ft.IconButton(
                        icon=ft.Icons.EDIT_OUTLINED,
                        icon_color=MUTED,
                        tooltip="Editar",
                        on_click=lambda e,
                        sid=row["id"]:
                            edit_session(sid),
                    ),

                    ft.IconButton(
                        icon=ft.Icons.DELETE_OUTLINE,
                        icon_color=DANGER,
                        tooltip="Excluir",
                        on_click=lambda e,
                        sid=row["id"]:
                            confirm_delete(sid),
                    ),
                ],
                vertical_alignment=(
                    ft.CrossAxisAlignment.CENTER
                ),
            ),

            padding=ft.Padding(
                0,
                13,
                0,
                13,
            ),

            border=ft.Border(
                bottom=ft.BorderSide(
                    1,
                    BORDER,
                )
            ),
        )

    # ========================================================
    # DASHBOARD
    # ========================================================

    dashboard_content = ft.Column(
        spacing=28,
        scroll=ft.ScrollMode.AUTO,
        expand=True,
    )

    def build_dashboard():

        s = db.stats()

        today_label = datetime.now().strftime(
            "%A, %d de %B"
        )

        # -----------------------------------------------
        # RESUMO DE HOJE
        # -----------------------------------------------

        today_summary = ft.Container(
            content=ft.Column(
                [
                    section_label(
                        "HOJE"
                    ),

                    ft.Container(
                        height=12
                    ),

                    ft.Text(
                        str(s["hoje"]),
                        size=34,
                        weight=ft.FontWeight.BOLD,
                        color=TEXT,
                    ),

                    ft.Text(
                        "sessões registradas",
                        size=12,
                        color=MUTED,
                    ),

                    ft.Container(
                        height=18
                    ),

                    divider(),

                    ft.Container(
                        height=15
                    ),

                    ft.Text(
                        format_minutes(
                            s["minutos_hoje"]
                        ),
                        size=22,
                        weight=ft.FontWeight.BOLD,
                        color=PRIMARY,
                    ),

                    ft.Text(
                        "de estudo hoje",
                        size=12,
                        color=MUTED,
                    ),
                ],
                spacing=0,
            ),

            bgcolor=SURFACE,
            border=ft.Border.all(
                1,
                BORDER,
            ),
            border_radius=10,
            padding=22,
            width=210,
        )

        # -----------------------------------------------
        # MATÉRIAS
        # -----------------------------------------------

        subject_controls = []

        if not s["top"]:

            subject_controls.append(
                ft.Container(
                    content=ft.Text(
                        "Registre algumas sessões para visualizar sua distribuição.",
                        size=13,
                        color=MUTED,
                    ),
                    padding=ft.Padding(
                        0,
                        15,
                        0,
                        15,
                    ),
                )
            )

        else:

            maior = max(
                v for _, v in s["top"]
            )

            for materia, minutos in s["top"]:

                subject_controls.append(
                    ft.Column(
                        [
                            ft.Row(
                                [
                                    ft.Text(
                                        materia,
                                        size=13,
                                        weight=ft.FontWeight.BOLD,
                                        color=TEXT,
                                    ),

                                    ft.Container(
                                        expand=True
                                    ),

                                    ft.Text(
                                        format_minutes(
                                            minutos
                                        ),
                                        size=12,
                                        color=MUTED,
                                    ),
                                ]
                            ),

                            ft.ProgressBar(
                                value=(
                                    minutos / maior
                                    if maior
                                    else 0
                                ),
                                color=PRIMARY,
                                bgcolor=PRIMARY_LIGHT,
                                height=5,
                            ),
                        ],
                        spacing=7,
                    )
                )

        subjects_panel = ft.Container(
            content=ft.Column(
                [
                    section_label(
                        "TEMPO POR MATÉRIA"
                    ),

                    ft.Container(
                        height=14
                    ),

                    *subject_controls,
                ],
                spacing=13,
            ),
            expand=True,
        )

        # -----------------------------------------------
        # SESSÕES RECENTES
        # -----------------------------------------------

        recent = db.all()

        recent_controls = []

        for row in recent[:5]:
            recent_controls.append(
                session_row(row)
            )

        if not recent_controls:

            recent_controls.append(
                ft.Container(
                    content=ft.Text(
                        "Nenhuma sessão registrada ainda.",
                        size=13,
                        color=MUTED,
                    ),
                    padding=ft.Padding(
                        0,
                        15,
                        0,
                        15,
                    ),
                )
            )

        recent_panel = ft.Container(
            content=ft.Column(
                [
                    section_label(
                        "ÚLTIMAS SESSÕES"
                    ),

                    ft.Container(
                        height=8
                    ),

                    *recent_controls,
                ],
                spacing=0,
            ),
            expand=True,
        )

        # -----------------------------------------------
        # CABEÇALHO
        # -----------------------------------------------

        dashboard_content.controls = [

            ft.Row(
                [
                    ft.Column(
                        [
                            ft.Text(
                                "BOM ESTUDO.",
                                size=11,
                                weight=ft.FontWeight.BOLD,
                                color=PRIMARY,
                                letter_spacing=2,
                            ),

                            ft.Text(
                                "Visão geral",
                                size=34,
                                weight=ft.FontWeight.BOLD,
                                color=TEXT,
                            ),

                            ft.Text(
                                today_label,
                                size=13,
                                color=MUTED,
                            ),
                        ],
                        spacing=2,
                    ),

                    ft.Container(
                        expand=True
                    ),

                    ft.Container(
                        content=ft.Column(
                            [
                                ft.Text(
                                    "TEMPO TOTAL",
                                    size=10,
                                    weight=ft.FontWeight.BOLD,
                                    color=MUTED,
                                    letter_spacing=1,
                                ),

                                ft.Text(
                                    format_minutes(
                                        s["minutos"]
                                    ),
                                    size=20,
                                    weight=ft.FontWeight.BOLD,
                                    color=TEXT,
                                ),
                            ],
                            spacing=2,
                        ),
                        padding=ft.Padding(
                            15,
                            8,
                            15,
                            8,
                        ),
                        border=ft.Border.all(
                            1,
                            BORDER,
                        ),
                        border_radius=7,
                    ),
                ],
                vertical_alignment=(
                    ft.CrossAxisAlignment.CENTER
                ),
            ),

            # TIMER + HOJE
            ft.Row(
                [
                    ft.Container(
                        content=timer_panel(),
                        expand=True,
                    ),

                    today_summary,
                ],
                spacing=18,
                vertical_alignment=(
                    ft.CrossAxisAlignment.START
                ),
            ),

            # MATÉRIAS
            simple_container(
                subjects_panel,
                padding=22,
            ),

            # SESSÕES
            simple_container(
                recent_panel,
                padding=22,
            ),
        ]

    # ========================================================
    # SESSÕES
    # ========================================================

    sessions_content = ft.Column(
        spacing=24,
        scroll=ft.ScrollMode.AUTO,
        expand=True,
    )

    search_field = ft.TextField(
        hint_text="Pesquisar matéria ou assunto",
        prefix_icon=ft.Icons.SEARCH,
        expand=True,
    )

    materia_filter = ft.Dropdown(
        width=180,
        value="Todas",
        options=[
            ft.DropdownOption(
                key="Todas",
                text="Todas",
            )
        ],
    )

    period_filter = ft.Dropdown(
        width=150,
        value="Todos",
        options=[
            ft.DropdownOption(
                key="Todos",
                text="Todos",
            ),
            ft.DropdownOption(
                key="Hoje",
                text="Hoje",
            ),
            ft.DropdownOption(
                key="7 dias",
                text="7 dias",
            ),
            ft.DropdownOption(
                key="30 dias",
                text="30 dias",
            ),
        ],
    )

    search_field.on_change = (
        lambda e: render()
    )

    materia_filter.on_change = (
        lambda e: render()
    )

    period_filter.on_change = (
        lambda e: render()
    )

    def update_materia_filter():

        values = [
            "Todas"
        ] + db.materias()

        materia_filter.options = [
            ft.DropdownOption(
                key=v,
                text=v,
            )
            for v in values
        ]

        if materia_filter.value not in values:
            materia_filter.value = "Todas"

    def build_sessions():

        update_materia_filter()

        rows = db.all(
            search=search_field.value or "",
            materia=materia_filter.value or "Todas",
            period=period_filter.value or "Todos",
        )

        rows_controls = [
            session_row(row)
            for row in rows
        ]

        if not rows_controls:

            rows_controls.append(
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Icon(
                                ft.Icons.SEARCH_OFF,
                                size=38,
                                color=MUTED,
                            ),

                            ft.Container(
                                height=8
                            ),

                            ft.Text(
                                "Nenhuma sessão encontrada.",
                                size=15,
                                weight=ft.FontWeight.BOLD,
                                color=TEXT,
                            ),

                            ft.Text(
                                "Altere os filtros ou registre uma nova sessão.",
                                size=12,
                                color=MUTED,
                            ),
                        ],
                        horizontal_alignment=(
                            ft.CrossAxisAlignment.CENTER
                        ),
                    ),
                    padding=35,
                    alignment=ft.Alignment(
                        0,
                        0,
                    ),
                )
            )

        sessions_content.controls = [

            ft.Row(
                [
                    page_title(
                        "Sessões",
                        "Seu histórico de estudo.",
                    ),

                    ft.Container(
                        expand=True
                    ),

                    ft.FilledButton(
                        "Nova sessão",
                        icon=ft.Icons.ADD,
                        style=ft.ButtonStyle(
                            bgcolor=PRIMARY,
                            color=ft.Colors.WHITE,
                            shape=ft.RoundedRectangleBorder(
                                radius=7
                            ),
                        ),
                        on_click=lambda e:
                            current_view_set(
                                "form"
                            ),
                    ),
                ],
                vertical_alignment=(
                    ft.CrossAxisAlignment.CENTER
                ),
            ),

            simple_container(
                ft.Row(
                    [
                        search_field,
                        materia_filter,
                        period_filter,
                    ],
                    spacing=10,
                ),
                padding=12,
            ),

            simple_container(
                ft.Column(
                    rows_controls,
                    spacing=0,
                ),
                padding=ft.Padding(
                    22,
                    5,
                    22,
                    5,
                ),
            ),
        ]

    # ========================================================
    # FORMULÁRIO
    # ========================================================

    form_content = ft.Column(
        spacing=24,
        scroll=ft.ScrollMode.AUTO,
        expand=True,
    )

    def build_form():

        form_content.controls = [

            ft.Row(
                [
                    ft.Column(
                        [
                            ft.Text(
                                "REGISTRO",
                                size=11,
                                weight=ft.FontWeight.BOLD,
                                color=PRIMARY,
                                letter_spacing=2,
                            ),

                            session_form_title,

                            ft.Text(
                                "Adicione uma sessão ao seu histórico.",
                                size=13,
                                color=MUTED,
                            ),
                        ],
                        spacing=3,
                    ),

                    ft.Container(
                        expand=True
                    ),
                ]
            ),

            simple_container(
                ft.Column(
                    [

                        ft.Row(
                            [
                                ft.Container(
                                    content=materia_field,
                                    expand=True,
                                ),

                                ft.Container(
                                    content=duracao_field,
                                    width=220,
                                ),
                            ],
                            spacing=14,
                        ),

                        assunto_field,

                        data_field,

                        ft.Container(
                            height=5
                        ),

                        divider(),

                        ft.Container(
                            height=12
                        ),

                        ft.Row(
                            [
                                ft.FilledButton(
                                    "Salvar sessão",
                                    icon=ft.Icons.CHECK,
                                    style=ft.ButtonStyle(
                                        bgcolor=PRIMARY,
                                        color=ft.Colors.WHITE,
                                        shape=ft.RoundedRectangleBorder(
                                            radius=7
                                        ),
                                    ),
                                    on_click=save_session,
                                ),

                                ft.OutlinedButton(
                                    "Limpar",
                                    icon=ft.Icons.CLEAR,
                                    style=ft.ButtonStyle(
                                        shape=ft.RoundedRectangleBorder(
                                            radius=7
                                        ),
                                    ),
                                    on_click=lambda e: (
                                        clear_form(),
                                        build_form(),
                                        page.update(),
                                    ),
                                ),
                            ],
                            spacing=10,
                        ),
                    ],
                    spacing=15,
                ),
                padding=25,
            ),
        ]

    # ========================================================
    # NAVEGAÇÃO LATERAL
    # ========================================================

    content_container = ft.Container(
        expand=True,
        padding=ft.Padding(
            40,
            32,
            40,
            30,
        ),
    )

    nav_title = ft.Column(
        [
            ft.Text(
                "FOCUS",
                size=11,
                weight=ft.FontWeight.BOLD,
                color="#A9BDB5",
                letter_spacing=2,
            ),

            ft.Text(
                "TRACK",
                size=22,
                weight=ft.FontWeight.BOLD,
                color=ft.Colors.WHITE,
                letter_spacing=1,
            ),

            ft.Container(
                height=8
            ),

            ft.Text(
                "Estude com intenção.",
                size=11,
                color="#9BAFA7",
            ),
        ],
        spacing=0,
    )

    nav_dashboard = ft.Container()
    nav_sessions = ft.Container()
    nav_form = ft.Container()

    def nav_item(
        label,
        icon,
        selected,
        on_click,
    ):

        return ft.Container(
            content=ft.Row(
                [
                    ft.Icon(
                        icon,
                        size=18,
                        color=(
                            ft.Colors.WHITE
                            if selected
                            else "#91A59D"
                        ),
                    ),

                    ft.Text(
                        label,
                        size=12,
                        weight=(
                            ft.FontWeight.BOLD
                            if selected
                            else ft.FontWeight.NORMAL
                        ),
                        color=(
                            ft.Colors.WHITE
                            if selected
                            else "#91A59D"
                        ),
                    ),
                ],
                spacing=12,
            ),

            padding=ft.Padding(
                13,
                11,
                13,
                11,
            ),

            bgcolor=(
                "#245246"
                if selected
                else None
            ),

            border_radius=6,

            on_click=on_click,
        )

    def rebuild_nav():

        nav_dashboard.content = nav_item(
            "Visão geral",
            ft.Icons.DASHBOARD_OUTLINED,
            current_view == "dashboard",
            lambda e:
                current_view_set(
                    "dashboard"
                ),
        )

        nav_sessions.content = nav_item(
            "Sessões",
            ft.Icons.HISTORY,
            current_view == "sessions",
            lambda e:
                current_view_set(
                    "sessions"
                ),
        )

        nav_form.content = nav_item(
            "Registrar",
            ft.Icons.ADD,
            current_view == "form",
            lambda e: (
                clear_form(),
                current_view_set(
                    "form"
                ),
            ),
        )

    sidebar = ft.Container(
        content=ft.Column(
            [
                nav_title,

                ft.Container(
                    height=38
                ),

                ft.Text(
                    "NAVEGAÇÃO",
                    size=9,
                    weight=ft.FontWeight.BOLD,
                    color="#71877F",
                    letter_spacing=1.5,
                ),

                ft.Container(
                    height=7
                ),

                nav_dashboard,
                nav_sessions,
                nav_form,

                ft.Container(
                    expand=True
                ),

                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text(
                                "DISCIPLINA > MOTIVAÇÃO",
                                size=9,
                                weight=ft.FontWeight.BOLD,
                                color="#71877F",
                                letter_spacing=1,
                            ),

                            ft.Text(
                                "Consistência vence\nintensidade.",
                                size=12,
                                color="#9BAFA7",
                                italic=True,
                            ),
                        ],
                        spacing=6,
                    ),
                    padding=ft.Padding(
                        5,
                        0,
                        5,
                        15,
                    ),
                ),
            ],
            spacing=3,
        ),
        width=220,
        bgcolor=SURFACE_DARK,
        padding=ft.Padding(
            25,
            30,
            20,
            20,
        ),
    )

    # ========================================================
    # CABEÇALHO SUPERIOR
    # ========================================================

    top_header = ft.Container(
        content=ft.Row(
            [
                ft.Text(
                    "FOCUS / TRACK",
                    size=10,
                    weight=ft.FontWeight.BOLD,
                    color=MUTED,
                    letter_spacing=1.5,
                ),

                ft.Container(
                    expand=True
                ),

                ft.Text(
                    datetime.now().strftime(
                        "%d.%m.%Y"
                    ),
                    size=11,
                    color=MUTED,
                ),
            ]
        ),

        padding=ft.Padding(
            40,
            15,
            40,
            15,
        ),

        border=ft.Border(
            bottom=ft.BorderSide(
                1,
                BORDER,
            )
        ),
    )

    # ========================================================
    # TROCA DE PÁGINAS
    # ========================================================

    def current_view_set(view):

        nonlocal current_view

        current_view = view

        rebuild_nav()

        if view == "dashboard":

            build_dashboard()

            content_container.content = (
                dashboard_content
            )

        elif view == "sessions":

            build_sessions()

            content_container.content = (
                sessions_content
            )

        elif view == "form":

            build_form()

            content_container.content = (
                form_content
            )

        page.update()

    def render():

        current_view_set(
            current_view
        )

    # ========================================================
    # LAYOUT FINAL
    # ========================================================

    body = ft.Row(
        [
            sidebar,

            ft.Container(
                content=ft.Column(
                    [
                        top_header,
                        content_container,
                    ],
                    spacing=0,
                    expand=True,
                ),
                expand=True,
            ),
        ],
        spacing=0,
        expand=True,
    )

    page.add(body)

    render()


# ============================================================
# START
# ============================================================

if __name__ == "__main__":
    ft.app(target=main)