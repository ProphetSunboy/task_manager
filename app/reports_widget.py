# app/reports_widget.py
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QListWidget,
    QDateEdit,
    QComboBox,
)
from PyQt5.QtCore import QDate, Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.ticker import MaxNLocator
from matplotlib.colors import LinearSegmentedColormap
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from .translations import tr
from .storage import load_tasks
from .tasks_widget import format_seconds


class ReportsWidget(QWidget):
    def __init__(self, settings=None):
        super().__init__()
        self.settings = settings or {}
        self.tasks = load_tasks()
        self._build_ui()
        self.apply_font_size()
        self.retranslateUi()
        self.populate_task_list()

    def _build_ui(self):
        self.layout = QVBoxLayout(self)

        # label + search
        self.search_label = QLabel()
        self.search = QLineEdit()
        self.search.textChanged.connect(self.filter_tasks)
        self.task_list = QListWidget()
        self.task_list.setMinimumHeight(120)

        self.layout.addWidget(self.search_label)
        self.layout.addWidget(self.search)
        self.layout.addWidget(self.task_list)

        # date controls
        date_layout = QHBoxLayout()
        self.start_date_label = QLabel()
        self.start_date = QDateEdit(calendarPopup=True)
        self.start_date.setDate(QDate.currentDate().addDays(-30))
        self.end_date_label = QLabel()
        self.end_date = QDateEdit(calendarPopup=True)
        self.end_date.setDate(QDate.currentDate())
        date_layout.addWidget(self.start_date_label)
        date_layout.addWidget(self.start_date)
        date_layout.addWidget(self.end_date_label)
        date_layout.addWidget(self.end_date)
        self.layout.addLayout(date_layout)

        # period
        period_layout = QHBoxLayout()
        self.period_label = QLabel()
        self.period_combo = QComboBox()
        period_layout.addWidget(self.period_label)
        period_layout.addWidget(self.period_combo)
        self.layout.addLayout(period_layout)

        # plot
        btn_row = QHBoxLayout()
        self.btn_plot = QPushButton()
        btn_row.addWidget(self.btn_plot)
        self.layout.addLayout(btn_row)

        self.figure = Figure(figsize=(10, 4))
        self.canvas = FigureCanvas(self.figure)
        self.time_info = QLabel()
        self.layout.addWidget(self.time_info)
        self.layout.addWidget(self.canvas)

        self.btn_plot.clicked.connect(self.plot_selected)

    def retranslateUi(self):
        self.search_label.setText(tr("Select a task:"))
        self.search.setPlaceholderText(tr("Search task..."))
        self.start_date_label.setText(tr("From:"))
        self.end_date_label.setText(tr("To:"))
        self.period_label.setText(tr("Period:"))
        # period items
        self.period_combo.clear()
        self.period_combo.addItems([tr("Day"), tr("Week"), tr("Month")])
        self.btn_plot.setText(tr("Build chart"))
        # ensure time_info is cleared
        self.time_info.setText("")

    def populate_task_list(self):
        # наполняем список задач (всегда берём из storage, чтобы учесть изменения)
        self.tasks = load_tasks()
        self.task_list.clear()
        for t in self.tasks:
            title = t.title or "(no title)"
            self.task_list.addItem(title)

    def refresh_data(self):
        """Обновляет данные графиков после изменения задач."""
        self.populate_task_list()

    def filter_tasks(self):
        text = self.search.text().lower()
        self.task_list.clear()
        for t in self.tasks:
            if text in (t.title or "").lower():
                self.task_list.addItem(t.title)

    def plot_selected(self):
        item = self.task_list.currentItem()
        if not item:
            return
        task = next((t for t in self.tasks if t.title == item.text()), None)
        if not task:
            return
        start = self.start_date.date().toPyDate()
        end = self.end_date.date().toPyDate()
        period = self.period_combo.currentText()
        self.plot_task(task, start, end, period)

    def plot_task(self, task, start_date, end_date, period):
        dates, spent_seconds, allocated_seconds = [], [], []
        now = datetime.now()
        current = start_date
        while current <= end_date:
            dates.append(current)
            spent = 0
            for s in task.sessions:
                start_s = s.start.date()
                end_s = s.end.date() if s.end else now.date()
                if start_s <= current <= end_s:
                    spent += ((s.end or now) - s.start).total_seconds()
            spent_seconds.append(spent)
            allocated_seconds.append(task.time_allocated * 60)
            current += timedelta(days=1)

        df = pd.DataFrame(
            {"date": dates, "spent": spent_seconds, "allocated": allocated_seconds}
        )
        df["date"] = pd.to_datetime(df["date"])

        # grouping by period
        if period == tr("Week"):
            df = df.groupby(pd.Grouper(key="date", freq="W-MON")).sum().reset_index()
        elif period == tr("Month"):
            df = df.groupby(pd.Grouper(key="date", freq="M")).sum().reset_index()

        if df.empty:
            self.time_info.setText(tr("No data for selected period."))
            self.figure.clear()
            self.canvas.draw()
            return

        total_spent = df["spent"].sum()
        total_alloc = df["allocated"].sum()
        self.time_info.setText(
            f"{tr('Total')}: {format_seconds(total_spent)} | {tr('Allocated')}: {format_seconds(total_alloc)}"
        )

        # draw
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.set_facecolor("#222831")
        self.figure.set_facecolor("#1a1a1a")

        x = np.arange(len(df))
        width = 0.4

        cmap_alloc = LinearSegmentedColormap.from_list(
            "blue_grad", ["#3399ff", "#007bff"]
        )
        cmap_spent = LinearSegmentedColormap.from_list(
            "green_grad", ["#2ecc71", "#1abc9c"]
        )

        bars1, bars2 = [], []
        for i in range(len(df)):
            b1 = ax.bar(
                x[i] - width / 2,
                df["allocated"].iloc[i] / 3600,
                width,
                color=cmap_alloc(0.8),
                alpha=0.8,
            )[0]
            b2 = ax.bar(
                x[i] + width / 2,
                df["spent"].iloc[i] / 3600,
                width,
                color=cmap_spent(0.8),
                alpha=0.9,
            )[0]
            bars1.append(b1)
            bars2.append(b2)

        # Сохраняем бары и создаём аннотацию, если её ещё нет
        self.tooltip = ax.annotate(
            "",
            xy=(0, 0),
            xytext=(0, 25),  # смещаем подсказку вниз, чтобы не перекрывала легенду
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=10,
            bbox=dict(
                boxstyle="round,pad=0.3",
                fc="#222831" if self.settings.get("dark_theme") else "white",
                alpha=0.9,
            ),
            color="white" if self.settings.get("dark_theme") else "black",
            arrowprops=dict(
                arrowstyle="->",
                color="#222831" if self.settings.get("dark_theme") else "black",
            ),
        )
        self.tooltip.set_visible(False)

        def format_hours(h):
            n = int(h)
            k = int((h - n) * 60)
            if tr.lang == "Русский":
                return f"{n} ч, {k} мин"
            else:
                return f"{n} h, {k} min"

        def on_motion(event):
            vis = self.tooltip.get_visible()
            if event.inaxes == ax:
                for bar, sec, label in zip(
                    bars1 + bars2,
                    list(df["allocated"]) + list(df["spent"]),
                    [tr("Allocated")] * len(bars1) + [tr("Spent")] * len(bars2),
                ):
                    cont, _ = bar.contains(event)
                    if cont:
                        text = f"{label}: {format_hours(sec / 3600)}"
                        self.tooltip.set_text(text)
                        self.tooltip.xy = (
                            bar.get_x() + bar.get_width() / 2,
                            bar.get_height(),
                        )

                        # базовое смещение вниз
                        offset_x, offset_y = 0, -25

                        # если близко к правому краю, смещаем влево
                        xlim = ax.get_xlim()
                        if event.xdata + 0.1 * (xlim[1] - xlim[0]) > xlim[1]:
                            offset_x = -50  # или подбираем динамически

                        self.tooltip.set_position((offset_x, offset_y))
                        self.tooltip.set_visible(True)
                        self.canvas.draw_idle()
                        return
            if vis:
                self.tooltip.set_visible(False)
                self.canvas.draw_idle()

        self.figure.canvas.mpl_connect("motion_notify_event", on_motion)

        ax.set_xticks(x)
        ax.set_xticklabels(
            [d.strftime("%d.%m") for d in df["date"]],
            rotation=45,
            ha="right",
            color="white",
        )
        ax.set_ylabel(tr("Hours"), color="white")
        ax.tick_params(axis="y", colors="white")
        ax.tick_params(axis="x", colors="white")
        ax.set_title(f"{tr('Report for task:')} {task.title}", color="white", pad=15)
        ax.yaxis.set_major_formatter(lambda x, _: f"{int(x)}h {int((x-int(x))*60)}m")
        ax.yaxis.set_major_locator(MaxNLocator(integer=True))
        ax.grid(color="#444", linestyle="--", alpha=0.5)
        if bars1 and bars2:
            ax.legend(
                [bars1[0], bars2[0]],
                [tr("Allocated"), tr("Spent")],
                facecolor="#2a2a2a",
                edgecolor="#444",
                labelcolor="white",
            )
        self.figure.tight_layout()
        self.figure.subplots_adjust(bottom=0.25)
        self.canvas.draw()

    def apply_font_size(self):
        font_size = (
            int(self.settings.get("font_size", 12))
            if getattr(self, "settings", None)
            else 12
        )
        font = self.font()
        font.setPointSize(font_size)
        self.setFont(font)
