# reports_widget.py
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
    def __init__(self):
        super().__init__()
        self.tasks = load_tasks()
        self.init_ui()
        self.apply_font_size()
        self.retranslateUi()

    def init_ui(self):
        self.layout = QVBoxLayout(self)

        self.search_label = QLabel()
        self.search = QLineEdit()
        self.search.textChanged.connect(self.filter_tasks)
        self.task_list = QListWidget()

        self.start_date_label = QLabel()
        self.start_date = QDateEdit(calendarPopup=True)
        self.start_date.setDate(QDate.currentDate().addDays(-30))

        self.end_date_label = QLabel()
        self.end_date = QDateEdit(calendarPopup=True)
        self.end_date.setDate(QDate.currentDate())

        self.period_label = QLabel()
        self.period_combo = QComboBox()

        self.btn_plot = QPushButton()
        self.figure = Figure(figsize=(10, 4))
        self.canvas = FigureCanvas(self.figure)
        self.time_info = QLabel()

        self.layout.addWidget(self.search_label)
        self.layout.addWidget(self.search)
        self.layout.addWidget(self.task_list)

        date_layout = QHBoxLayout()
        date_layout.addWidget(self.start_date_label)
        date_layout.addWidget(self.start_date)
        date_layout.addWidget(self.end_date_label)
        date_layout.addWidget(self.end_date)
        self.layout.addLayout(date_layout)

        period_layout = QHBoxLayout()
        period_layout.addWidget(self.period_label)
        period_layout.addWidget(self.period_combo)
        self.layout.addLayout(period_layout)

        btn_row = QHBoxLayout()
        btn_row.addWidget(self.btn_plot)
        self.layout.addLayout(btn_row)
        self.layout.addWidget(self.time_info)
        self.layout.addWidget(self.canvas)

        self.btn_plot.clicked.connect(self.plot_selected)

    def retranslateUi(self):
        self.search_label.setText(tr("Select a task:"))
        self.search.setPlaceholderText(tr("Search task..."))
        self.start_date_label.setText(tr("From:"))
        self.end_date_label.setText(tr("To:"))
        self.period_label.setText(tr("Period:"))
        self.period_combo.clear()
        self.period_combo.addItems([tr("Day"), tr("Week"), tr("Month")])
        self.btn_plot.setText(tr("Build chart"))
        self.time_info.setText("")

    def filter_tasks(self):
        text = self.search.text().lower()
        self.task_list.clear()
        for t in self.tasks:
            if text in t.title.lower():
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

        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.set_facecolor("#222831")
        self.figure.set_facecolor("#1a1a1a")

        x = np.arange(len(df))
        width = 0.4
        bars1 = [
            ax.bar(
                x[i] - width / 2,
                df["allocated"].iloc[i] / 3600,
                width,
                color=LinearSegmentedColormap.from_list(
                    "blue_grad", ["#3399ff", "#007bff"]
                )(0.8),
                alpha=0.8,
            )[0]
            for i in range(len(df))
        ]
        bars2 = [
            ax.bar(
                x[i] + width / 2,
                df["spent"].iloc[i] / 3600,
                width,
                color=LinearSegmentedColormap.from_list(
                    "green_grad", ["#2ecc71", "#1abc9c"]
                )(0.8),
                alpha=0.9,
            )[0]
            for i in range(len(df))
        ]

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
        font_size = getattr(self, "settings", {}).get("font_size", 12)
        font = self.font()
        font.setPointSize(font_size)
        self.setFont(font)
