from __future__ import annotations

from datetime import date, datetime

from PySide6.QtCore import QRectF, QSize, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QGuiApplication, QKeyEvent, QMouseEvent, QPainter, QPainterPath, QTextCursor
from PySide6.QtWidgets import (
    QFrame,
    QLineEdit,
    QPlainTextEdit,
    QVBoxLayout,
    QWidget,
)

from origami.context import Context
from origami.store import Task
from origami.ui import icons
from origami.ui.components import (
    Card,
    CheckDot,
    ElidedLabel,
    EmptyState,
    IconLabel,
    OutsideClick,
    Page,
    PriorityPill,
    button,
    confirm,
    hbox,
    icon_button,
    label,
    pick_reminder,
    priority_menu,
    retone,
    show_if,
    show_menu,
    vbox,
    when_text,
)
from origami.ui.theme import PRIORITY_COLORS, event_tint, theme

AUTOSAVE_MS = 400
COMPLETE_DELAY_MS = 350
INDENT = 48
RADIUS = 11
SHOW_DONE = "tasks_show_done"
ACTION_GAP = 10


def done_text(stamp: datetime) -> str:
    delta = (date.today() - stamp.date()).days
    if delta == 0:
        return "Today"
    return "Yesterday" if delta == 1 else f"{stamp.day} {stamp:%b}"


class InlineEdit(QLineEdit):
    cancelled = Signal()
    focused = Signal(bool)

    def __init__(self, text: str = "", placeholder: str = "", *, flat: bool = True) -> None:
        super().__init__(text)
        self.setPlaceholderText(placeholder)
        self.setMaxLength(200)
        self.setProperty("flat", flat)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self.cancelled.emit()
        else:
            super().keyPressEvent(event)

    def focusInEvent(self, event) -> None:
        super().focusInEvent(event)
        self.focused.emit(True)

    def focusOutEvent(self, event) -> None:
        super().focusOutEvent(event)
        self.focused.emit(False)


def retain(widget: QWidget) -> None:
    policy = widget.sizePolicy()
    policy.setRetainSizeWhenHidden(True)
    widget.setSizePolicy(policy)


class NotesEdit(QPlainTextEdit):
    cancelled = Signal()
    blurred = Signal()

    def __init__(self, text: str) -> None:
        super().__init__(text)
        self.setObjectName("RowNotes")
        self.setProperty("flat", True)
        self.setPlaceholderText("Notes")
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.document().documentLayout().documentSizeChanged.connect(self._fit)
        self._fit()

    def _fit(self) -> None:
        doc = self.document()
        lines = max(1, int(doc.size().height()))
        height = lines * self.fontMetrics().lineSpacing() + 2 * int(doc.documentMargin())
        self.setFixedHeight(min(max(height, 40), 120))

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self.cancelled.emit()
        else:
            super().keyPressEvent(event)

    def focusOutEvent(self, event) -> None:
        super().focusOutEvent(event)
        self.blurred.emit()


_action_size: QSize | None = None


def action_size() -> QSize:
    """Size of one hover action button, measured once so rows can reserve room without building them."""
    global _action_size
    if _action_size is None:
        probe = icon_button("trash", "", size=16)
        probe.ensurePolished()
        _action_size = probe.sizeHint()
        probe.deleteLater()
    return _action_size


class TaskRow(QFrame):
    opened = Signal(int)
    completed = Signal(int)
    restored = Signal(int)
    renamed = Signal(int, str)
    notes_edited = Signal(int, str)
    removed = Signal(int)
    prioritized = Signal(int, int)
    reminder_set = Signal(int, object)  # task id, datetime | None

    def __init__(self, task: Task, *, first: bool, last: bool, rule: int | None = None) -> None:
        super().__init__()
        self.task = task
        self._first, self._last = first, last
        self._rule = rule  # left inset of the hairline above this row; None = no line
        self._editing = False
        self._saved = task.notes
        self._click = QTimer(self, singleShot=True, timeout=lambda: self.opened.emit(self.task.id))
        self.setAttribute(Qt.WidgetAttribute.WA_Hover)

        self.check = CheckDot(task.done, 20, "Mark as not done" if task.done else "Complete task")
        if not task.done:
            self.check.priority = task.priority
        self.title = ElidedLabel(task.title, "taskdone" if task.done else "task")
        if task.done:
            self._strike()
        # The inline editor and hover buttons are built on first use: most rows never need them.
        self.editor: InlineEdit | None = None
        self.flag: QWidget | None = None
        preview = "" if task.done else next((s.strip() for s in task.notes.splitlines() if s.strip()), "")
        self.preview = ElidedLabel(preview, "muted")
        show_if(self.preview, bool(preview))
        self.text = text = vbox(self.title, self.preview, spacing=2)
        if task.remind_at and not task.done:
            late = task.remind_at < datetime.now()
            when = label(when_text(task.remind_at), "caption")
            retone(when, "danger" if late else "accent")
            text.addLayout(hbox(IconLabel("bell", "danger" if late else "accent", 12), when, None, spacing=4))
        text.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        count = 1 if task.done else 3
        size = action_size()
        self.actions = QWidget()
        self.actions.setFixedSize(count * size.width() + (count - 1) * ACTION_GAP, size.height())
        retain(self.actions)
        self.actions.hide()
        trailing: list[QWidget] = []
        if task.done and task.done_at:
            trailing.append(label(done_text(task.done_at), "caption"))

        self.head = head = QWidget()
        head.setMinimumHeight(50)
        head.setLayout(hbox(self.check, text, *trailing, self.actions, spacing=10, margins=(18, 8, 12, 8)))
        head.layout().setStretch(1, 1)

        self.notes_box = QWidget()
        self.notes_box.hide()
        self.notes: NotesEdit | None = None
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        outer.addWidget(head)
        outer.addWidget(self.notes_box)

        if task.done:
            self.check.clicked.connect(lambda: self.restored.emit(task.id))
        else:
            self.check.clicked.connect(self._complete)

    def set_edges(self, first: bool, last: bool, rule: int | None) -> None:
        if (first, last, rule) != (self._first, self._last, self._rule):
            self._first, self._last, self._rule = first, last, rule
            self.update()

    def _build_actions(self) -> None:
        tid = self.task.id
        buttons: list[QWidget] = []
        if not self.task.done:
            self.flag = icon_button("flag", "Set priority", self._pick_priority, size=16)
            buttons += [icon_button("bell", "Remind me", self._pick_reminder, size=16), self.flag]
        buttons.append(icon_button("trash", "Delete task", lambda: self.removed.emit(tid), size=16))
        self.actions.setLayout(hbox(*buttons, spacing=ACTION_GAP))

    def _strike(self) -> None:
        font = self.title.font()
        font.setStrikeOut(True)
        self.title.setFont(font)

    def _complete(self) -> None:
        self.check.setEnabled(False)
        self._strike()
        self.completed.emit(self.task.id)

    def _build_notes(self) -> NotesEdit:
        notes = NotesEdit(self.task.notes)
        self._autosave = QTimer(self, singleShot=True, interval=AUTOSAVE_MS)
        self._autosave.timeout.connect(self.flush)
        notes.textChanged.connect(self._autosave.start)
        notes.blurred.connect(self.flush)
        notes.cancelled.connect(lambda: self.opened.emit(self.task.id))
        self.notes_box.setLayout(hbox(notes, margins=(INDENT - 4, 0, 16, 10)))
        self.notes = notes
        return notes

    def set_expanded(self, expanded: bool) -> None:
        if self.task.done or expanded != self.notes_box.isHidden():
            return
        if expanded:
            notes = self.notes or self._build_notes()
            self.head.setMinimumHeight(46)
            self.notes_box.show()
            self.preview.hide()
            notes.setFocus()
            notes.moveCursor(QTextCursor.MoveOperation.End)
            return
        self.flush()
        self.head.setMinimumHeight(50)
        self.notes_box.hide()
        line = next((s.strip() for s in self.notes.toPlainText().splitlines() if s.strip()), "")
        self.preview.setText(line)
        self.preview.setVisible(bool(line))

    def flush(self) -> None:
        if self.notes is None:
            return
        self._autosave.stop()
        text = self.notes.toPlainText().strip()
        if text != self._saved.strip():
            self._saved = text
            self.notes_edited.emit(self.task.id, text)

    def _pick_priority(self) -> None:
        tid = self.task.id
        menu = priority_menu(self, self.task.priority, lambda level: self.prioritized.emit(tid, level))
        show_menu(menu, self.flag or self)

    def _pick_reminder(self) -> None:
        tid = self.task.id
        pick_reminder(self, self.task.remind_at, lambda when: self.reminder_set.emit(tid, when))

    def _sync_hover(self, hover: bool) -> None:
        if hover and self.actions.layout() is None:
            self._build_actions()
        self.actions.setVisible(hover)
        self.update()

    def enterEvent(self, event) -> None:
        self._sync_hover(True)
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        self._sync_hover(False)
        super().leaveEvent(event)

    def paintEvent(self, event) -> None:
        hover = self.underMouse()
        tinted = bool(self.task.priority) and not self.task.done
        if not hover and not tinted and self._rule is None:
            return
        painter = QPainter(self)
        if hover or tinted:
            if tinted:
                color = QColor(event_tint(theme.palette, self.task.priority)[1 if hover else 0])
            else:
                color = QColor(theme.palette.raised)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setClipRect(self.rect())
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(color)
            top, bottom = 0 if self._first else -RADIUS, 0 if self._last else RADIUS
            path = QPainterPath()
            path.addRoundedRect(QRectF(self.rect()).adjusted(0, top, 0, bottom), RADIUS, RADIUS)
            painter.drawPath(path)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        if self._rule is not None:
            painter.fillRect(self._rule, 0, self.width() - self._rule, 1, QColor(theme.palette.border))

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton and not self._editing and not self.task.done:
            self._click.start(QGuiApplication.styleHints().mouseDoubleClickInterval())

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton and not self.task.done:
            self._click.stop()
            self._begin_edit()

    def _ensure_editor(self) -> InlineEdit:
        if self.editor is None:
            editor = InlineEdit(self.task.title)
            editor.setObjectName("RowEdit")
            editor.hide()
            editor.editingFinished.connect(lambda: self._finish(True))
            editor.cancelled.connect(lambda: self._finish(False))
            self._outside = OutsideClick(editor, lambda: self._finish(True))
            self.text.insertWidget(1, editor)
            self.editor = editor
        return self.editor

    def _begin_edit(self) -> None:
        if self._editing:
            return
        editor = self._ensure_editor()
        self._editing = True
        self.title.hide()
        editor.setText(self.task.title)
        editor.show()
        editor.setFocus()
        editor.selectAll()
        self._outside.start()

    def _finish(self, save: bool) -> None:
        if not self._editing or self.editor is None:
            return
        self._editing = False
        self._outside.stop()
        text = self.editor.text().strip()
        self.editor.hide()
        self.title.show()
        if save and text and text != self.task.title:
            self.renamed.emit(self.task.id, text)


class Disclosure(QFrame):
    clicked = Signal()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()


class Composer(QFrame):
    """New-task bar: text field, priority picker and Add button."""

    submitted = Signal(str, int)

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("Composer")
        self.priority = 0
        self.input = InlineEdit(placeholder="Add a task and press Enter", flat=False)
        self.input.setObjectName("TaskInput")
        self.input.focused.connect(self._on_focus)
        self.input.returnPressed.connect(self._submit)
        self.input.cancelled.connect(self.input.clear)
        self._plus = IconLabel("plus", "faint", 18)
        self.flag = button("Normal", "ghost", on_click=self._pick)
        self.flag.setProperty("size", "sm")
        self.flag.setToolTip("Priority")
        self.flag.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        add = button("Add task", on_click=self._submit)
        add.setProperty("size", "sm")
        add.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setLayout(hbox(self._plus, self.input, self.flag, add, spacing=8, margins=(14, 4, 6, 4)))
        theme.changed.connect(self._tint)
        self._tint()

    def _tint(self) -> None:
        color = PRIORITY_COLORS(theme.palette)[self.priority] if self.priority else theme.palette.muted
        self.flag.setIcon(icons.icon("flag", color, 14))
        self.flag.setText(PriorityPill.NAMES[self.priority])

    def _pick(self) -> None:
        menu = priority_menu(self, self.priority, self._set_priority)
        show_menu(menu, self.flag)

    def _set_priority(self, level: int) -> None:
        self.priority = level
        self._tint()
        self.input.setFocus()

    def _on_focus(self, focused: bool) -> None:
        self._plus.set_color("accent" if focused else "faint")
        self.setProperty("active", focused)
        self.style().unpolish(self)
        self.style().polish(self)

    def _submit(self) -> None:
        text = self.input.text().strip()
        if not text:
            self.input.setFocus()
            return
        self.input.clear()
        self.submitted.emit(text, self.priority)
        self._set_priority(0)


class TasksPage(Page):
    def __init__(self, ctx: Context) -> None:
        super().__init__(ctx, "Tasks")
        self._open: int | None = None
        self._quiet = False
        self._rows: dict[int, TaskRow] = {}

        self.composer = Composer()
        self.composer.submitted.connect(self._add)
        self.input = self.composer.input

        # Persistent containers: a render only swaps the rows whose task actually changed.
        self.pending_card = self._list_card()
        self.empty_card = Card()
        empty = EmptyState("circle-check", "All done", "Add a task above to get started.")
        self.empty_card.body.addWidget(empty)
        self.done_section = QWidget()
        self._chevron = IconLabel("chevron-right", "faint", 16)
        self._done_count = label("", "count")
        self._clear_button = button("Clear", "ghost", on_click=self._clear_done)
        self._clear_button.setProperty("size", "sm")
        head = Disclosure()
        head.setCursor(Qt.CursorShape.PointingHandCursor)
        head.setMinimumHeight(34)
        head.setAccessibleName("Show or hide completed tasks")
        head.clicked.connect(self._toggle_done_section)
        head.setLayout(
            hbox(
                self._chevron,
                label("Completed", "section"),
                self._done_count,
                None,
                self._clear_button,
                spacing=8,
                margins=(4, 0, 0, 0),
            )
        )
        self.done_card = self._list_card()
        self.done_section.setLayout(vbox(head, self.done_card, spacing=8, margins=(0, 20, 0, 0)))

        self.content = vbox(self.pending_card, self.empty_card, self.done_section, spacing=0)
        self.body.setSpacing(14)
        self.body.addWidget(self.composer)
        self.body.addLayout(self.content)

        ctx.store.changed.connect(self._on_changed)
        self._render()

    @staticmethod
    def _list_card() -> Card:
        card = Card()
        card.body.setContentsMargins(0, 0, 0, 0)
        card.body.setSpacing(0)
        return card

    def focus_input(self) -> None:
        self.input.setFocus()

    def on_show(self) -> None:
        self._render()

    def hideEvent(self, event) -> None:
        self._flush()
        super().hideEvent(event)

    def _on_changed(self, domain: str) -> None:
        if domain == "tasks" and not self._quiet and self.live():
            self._render()

    def _write(self, task_id: int, *, quiet: bool = False, **fields: object) -> None:
        task = self.ctx.store.task(task_id)
        if task is None:
            return
        values = {"title": task.title, "notes": task.notes, **fields}
        self._quiet = quiet
        try:
            self.ctx.store.update_task(task_id, **values)
        finally:
            self._quiet = False

    def _flush(self) -> None:
        if (row := self._rows.get(self._open)) is not None:
            row.flush()

    def _add(self, text: str, priority: int) -> None:
        self.ctx.store.add_task(text, priority=priority)

    def _toggle_open(self, task_id: int) -> None:
        self._open = None if self._open == task_id else task_id
        for tid, row in self._rows.items():
            row.set_expanded(tid == self._open)

    def _complete(self, task_id: int) -> None:
        QTimer.singleShot(COMPLETE_DELAY_MS, lambda: self.ctx.store.set_done(task_id, True))

    def _set_reminder(self, task_id: int, when: datetime | None) -> None:
        self.ctx.store.set_task_reminder(task_id, when)
        self.ctx.toast(f"Reminder set for {when_text(when)}" if when else "Reminder removed")

    def _remove(self, task_id: int) -> None:
        if self._open == task_id:
            self._open = None
        self.ctx.store.delete_task(task_id)
        self.ctx.toast("Task deleted")

    def _clear_done(self) -> None:
        done, _ = self.ctx.store.task_counts()
        noun = "task" if done == 1 else "tasks"
        text = f"Remove {done} completed {noun}? This can't be undone."
        if confirm(self, "Clear completed tasks", text, "Clear"):
            self.ctx.store.clear_done()
            self.ctx.toast("Cleared completed tasks")

    def _show_done(self) -> bool:
        return bool(self.ctx.store.get_int(SHOW_DONE, 0))

    def _toggle_done_section(self) -> None:
        self.ctx.store.set(SHOW_DONE, 0 if self._show_done() else 1)
        self._render()

    def _render(self) -> None:
        self._flush()
        tasks = self.ctx.store.tasks()
        pending = [t for t in tasks if not t.done]
        done = [t for t in tasks if t.done]
        show = self._show_done()
        old, self._rows = self._rows, {}
        self._fill(self.pending_card, pending, old)
        self._fill(self.done_card, done if show else [], old)
        for row in old.values():  # rows whose task changed or disappeared
            row.hide()
            row.setParent(None)
            row.deleteLater()
        show_if(self.pending_card, bool(pending))
        show_if(self.empty_card, not pending)
        show_if(self.done_section, bool(done))
        show_if(self.done_card, show and bool(done))
        show_if(self._clear_button, show)
        self._chevron.set_name("chevron-down" if show else "chevron-right")
        self._done_count.setText(str(len(done)))
        if self._open in self._rows:
            self._rows[self._open].set_expanded(True)
        else:
            self._open = None

    def _fill(self, card: Card, tasks: list[Task], old: dict[int, TaskRow]) -> None:
        """Lay out `tasks` in `card`, reusing rows from `old` whose task is unchanged (taken out of `old`)."""
        body = card.body
        while body.takeAt(0) is not None:  # rows stay parented to the card; unused ones are freed later
            pass
        for i, task in enumerate(tasks):
            first, last = i == 0, i == len(tasks) - 1
            rule = None
            if i:  # coloured rows run edge to edge, so the hairline between them does too
                tinted = any(t.priority and not t.done for t in (tasks[i - 1], task))
                rule = 0 if tinted else INDENT
            row = old.get(task.id)
            if row is not None and row.task == task:
                del old[task.id]
                row.set_edges(first, last, rule)
            else:
                row = self._make_row(task, first, last, rule)
            self._rows[task.id] = row
            body.addWidget(row)

    def _make_row(self, task: Task, first: bool, last: bool, rule: int | None) -> TaskRow:
        row = TaskRow(task, first=first, last=last, rule=rule)
        row.removed.connect(self._remove)
        if task.done:
            row.restored.connect(lambda tid: self.ctx.store.set_done(tid, False))
            return row
        row.opened.connect(self._toggle_open)
        row.completed.connect(self._complete)
        row.prioritized.connect(lambda tid, level: self.ctx.store.set_task_priority(tid, level))
        row.reminder_set.connect(self._set_reminder)
        row.renamed.connect(lambda tid, text: self.ctx.store.rename_task(tid, text))
        row.notes_edited.connect(self._save_notes)
        return row

    def _save_notes(self, task_id: int, text: str) -> None:
        # Quiet: the open row already shows the text. Its task is refreshed so later renders keep it.
        self._write(task_id, quiet=True, notes=text)
        row, task = self._rows.get(task_id), self.ctx.store.task(task_id)
        if row is not None and task is not None:
            row.task = task
