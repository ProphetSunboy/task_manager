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
from PyQt5.QtCore import QDate
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
from matplotlib.colors import LinearSegmentedColormap

# Зависимости проекта
from .storage import load_tasks
from .tasks_widget import format_seconds


class ReportsWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        self.search = QLineEdit()
        self.search.setPlaceholderText("Поиск задачи...")
        self.search.textChanged.connect(self.filter_tasks)

        self.task_list = QListWidget()
        self.tasks = load_tasks()
        for t in self.tasks:
            self.task_list.addItem(t.title)

        date_layout = QHBoxLayout()
        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDate(QDate.currentDate().addDays(-30))
        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDate(QDate.currentDate())
        date_layout.addWidget(QLabel("С:"))
        date_layout.addWidget(self.start_date)
        date_layout.addWidget(QLabel("По:"))
        date_layout.addWidget(self.end_date)

        period_layout = QHBoxLayout()
        period_layout.addWidget(QLabel("Период:"))
        self.period_combo = QComboBox()
        self.period_combo.addItems(["День", "Неделя", "Месяц"])
        period_layout.addWidget(self.period_combo)

        btn_row = QHBoxLayout()
        self.btn_plot = QPushButton("Построить график")
        btn_row.addWidget(self.btn_plot)

        self.figure = Figure(figsize=(10, 4))
        self.canvas = FigureCanvas(self.figure)
        self.time_info = QLabel("")

        layout.addWidget(QLabel("Выберите задачу:"))
        layout.addWidget(self.search)
        layout.addWidget(self.task_list)
        layout.addLayout(date_layout)
        layout.addLayout(period_layout)
        layout.addLayout(btn_row)
        layout.addWidget(self.time_info)
        layout.addWidget(self.canvas)

        self.btn_plot.clicked.connect(self.plot_selected)

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
        title = item.text()
        task = next((t for t in self.tasks if t.title == title), None)
        if not task:
            return
        start = self.start_date.date().toPyDate()
        end = self.end_date.date().toPyDate()
        period = self.period_combo.currentText()
        self.plot_task(task, start, end, period)

    def plot_task(self, task, start_date, end_date, period):
        from matplotlib.ticker import MaxNLocator
        from matplotlib.colors import LinearSegmentedColormap
        import numpy as np
        import pandas as pd
        from datetime import datetime, timedelta
        import matplotlib.pyplot as plt

        # Подготовка данных
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

        if period == "Неделя":
            df = df.groupby(pd.Grouper(key="date", freq="W-MON")).sum().reset_index()
        elif period == "Месяц":
            df = df.groupby(pd.Grouper(key="date", freq="M")).sum().reset_index()

        if df.empty:
            self.time_info.setText("Нет данных для выбранного периода.")
            self.figure.clear()
            self.canvas.draw()
            return

        total_spent = df["spent"].sum()
        total_alloc = df["allocated"].sum()
        self.time_info.setText(
            f"Общее время: {format_seconds(total_spent)} | Выделено: {format_seconds(total_alloc)}"
        )

        # Построение графика
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

        bars1 = [
            ax.bar(
                x[i] - width / 2,
                df["allocated"].iloc[i] / 3600,
                width,
                color=cmap_alloc(0.8),
                alpha=0.8,
            )[0]
            for i in range(len(df))
        ]
        bars2 = [
            ax.bar(
                x[i] + width / 2,
                df["spent"].iloc[i] / 3600,
                width,
                color=cmap_spent(0.8),
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
        ax.set_ylabel("Часы", color="white")
        ax.tick_params(axis="y", colors="white")
        ax.tick_params(axis="x", colors="white")
        ax.set_title(f"Отчёт по задаче: {task.title}", color="white", pad=15)
        ax.yaxis.set_major_formatter(
            plt.FuncFormatter(lambda x, _: f"{int(x)}h {int((x-int(x))*60)}m")
        )
        ax.yaxis.set_major_locator(MaxNLocator(integer=True))
        ax.grid(color="#444", linestyle="--", alpha=0.5)
        ax.legend(
            [bars1[0], bars2[0]],
            ["Выделено", "Затрачено"],
            facecolor="#2a2a2a",
            edgecolor="#444",
            labelcolor="white",
        )
        self.figure.tight_layout()
        self.figure.subplots_adjust(bottom=0.25)

        # ---- Подсказки ----
        annot = ax.annotate(
            "",
            xy=(0, 0),
            xytext=(10, 10),
            textcoords="offset points",
            ha="center",
            va="bottom",
            bbox=dict(boxstyle="round", fc="#f8f9fa", ec="#000", lw=1),
            arrowprops=dict(arrowstyle="->", color="#ccc"),
        )
        annot.set_visible(False)

        def update_annot(bar, label, value):
            x = bar.get_x() + bar.get_width() / 2
            y = bar.get_height()
            annot.xy = (x, y)

            text = f"{label}: {format_seconds(value)}"
            annot.set_text(text)

            # --- координаты в пикселях ---
            x_px, y_px = ax.transData.transform((x, y))
            canvas_w, canvas_h = self.canvas.width(), self.canvas.height()

            # стандартное смещение (право и вверх)
            dx, dy = 10, 10

            # если подсказка рисуется у правого края → рисуем левее
            # если совсем у левого края → немного вправо
            if x_px + 100 > canvas_w:
                dx = -50
            elif x_px < 100:
                dx = 20

            # если слишком высоко → немного вниз
            if y_px > canvas_h - 100:
                dy = -40

            annot.set_position((dx, dy))
            annot.set_visible(True)

        def hover(event):
            visible = annot.get_visible()
            if event.inaxes != ax:
                if visible:
                    annot.set_visible(False)
                    self.canvas.draw_idle()
                return

            found = False
            for i, bar in enumerate(bars1):
                if bar.contains(event)[0]:
                    update_annot(bar, "Выделено", df["allocated"].iloc[i])
                    found = True
                    break

            if not found:
                for i, bar in enumerate(bars2):
                    if bar.contains(event)[0]:
                        update_annot(bar, "Затрачено", df["spent"].iloc[i])
                        found = True
                        break

            if found:
                self.canvas.draw_idle()
            elif visible:
                annot.set_visible(False)
                self.canvas.draw_idle()

        self.canvas.mpl_connect("motion_notify_event", hover)
        self.canvas.draw()
