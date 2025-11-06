
import asyncio
import math
import time
from flet import (
    app,
    Page,
    Text,
    TextField,
    ElevatedButton,
    IconButton,
    Icons,
    Row,
    Column,
    Container,
    ProgressRing,
    ProgressBar,
    Card,
    padding,
    alignment,
    MainAxisAlignment,
    CrossAxisAlignment,
    border,
    BorderSide,
    Colors,
)


class CountdownTimer:
    def __init__(self, page: Page, name: str, default_seconds: int = 60):
        self.page = page
        self.name = name
        self.default_seconds = default_seconds
        self.total_seconds = default_seconds
        self.remaining = default_seconds
        self.running = False
        self._task = None

        # UI
        self.input = TextField(value=str(self.default_seconds), label="Start seconds", width=160)
        self.start_btn = ElevatedButton("Start", on_click=self.start)
        self.pause_btn = ElevatedButton("Pause", on_click=self.pause)
        self.reset_btn = ElevatedButton("Reset", on_click=self.reset)
        self.time_text = Text(self._format_time(self.remaining), size=24)
        self.progress_ring = ProgressRing(value=self._progress_fraction())
        self.progress_bar = ProgressBar(width=300, height=10, value=self._progress_fraction())

        # container for the timer UI so we can swap views
        self.view = Column([
            Row([Text(f"{self.name}", size=20)], alignment=MainAxisAlignment.START),
            Row([
                Text("Set start seconds:"),
                self.input,
            ], alignment=MainAxisAlignment.START),
            Row([
                self.start_btn,
                self.pause_btn,
                self.reset_btn,
            ], spacing=12),
            Row([
                self.time_text,
                self.progress_ring,
            ], alignment=MainAxisAlignment.SPACE_BETWEEN),
            self.progress_bar,
        ], tight=True, spacing=12)

    def _format_time(self, s: int) -> str:
        if s < 0:
            s = 0
        m = s // 60
        sec = s % 60
        return f"{m:02d}:{sec:02d}"

    def _progress_fraction(self) -> float:
        if self.total_seconds <= 0:
            return 0.0
        return max(0.0, min(1.0, (self.total_seconds - self.remaining) / self.total_seconds))

    def start(self, e=None):
        # parse input
        try:
            val = int(self.input.value)
            if val <= 0:
                return
            # if timer was never set (or we want to override), set total_seconds
            if self.remaining <= 0 or val != self.total_seconds:
                self.total_seconds = val
                self.remaining = val
                self._sync_ui()
        except Exception:
            # ignore invalid input
            pass

        if not self.running:
            self.running = True
            # spawn background task
            if self._task is None or self._task.done():
                # page.run_task expects an async function
                self._task = self.page.run_task(self._run)
            self._sync_ui()

    def pause(self, e=None):
        if self.running:
            self.running = False
            self._sync_ui()

    def reset(self, e=None):
        self.running = False
        self.remaining = self.total_seconds
        self._sync_ui()

    async def _run(self):
        try:
            last_tick = None
            while True:
                # short sleep to remain responsive
                await asyncio.sleep(0.1)

                if not self.running:
                    # keep task alive while paused
                    await asyncio.sleep(0.1)
                    continue

                now = time.monotonic()
                if last_tick is None:
                    last_tick = now
                elapsed = now - last_tick
                last_tick = now

                # decrement by real elapsed seconds
                self.remaining -= elapsed
                if self.remaining <= 0:
                    self.remaining = 0
                    self.running = False
                    self._sync_ui()
                    break

                self._sync_ui()
        except Exception as exc:
            # keep UI consistent on unexpected errors
            self.running = False
            self._sync_ui()
            print("Timer task error:", exc)

    def _sync_ui(self):
        # update UI elements; truncate remaining to int seconds for display
        self.time_text.value = self._format_time(math.ceil(self.remaining))
        frac = self._progress_fraction()
        # ProgressRing expects value between 0 and 1
        self.progress_ring.value = frac
        self.progress_bar.value = frac
        # enable/disable buttons accordingly
        self.start_btn.disabled = self.running
        self.pause_btn.disabled = not self.running
        self.reset_btn.disabled = (self.remaining == self.total_seconds and not self.running)
        # push update to the page
        try:
            self.page.update()
        except Exception:
            pass


def main(page: Page):
    page.title = "Multi Countdown Timers (drawer navigation)"
    page.horizontal_alignment = "stretch"
    page.padding = 10

    # three timers
    timers = [CountdownTimer(page, f"Timer {i+1}", default_seconds=60*(i+1)) for i in range(3)]

    # a container where the selected timer view will be shown
    content_container = Container(content=timers[0].view, expand=True, padding=10)

    selected_index = {"idx": 0}  # mutable closure

    def show_timer(i):
        selected_index['idx'] = i
        content_container.content = timers[i].view
        page.update()

    # left "drawer" (a vertical column) with nav buttons
    drawer_width = 200
    drawer = Column([
        Row([Text("Timers", size=18)], alignment=MainAxisAlignment.CENTER),
        Column([
            ElevatedButton(f"Timer {i+1}", on_click=lambda e, i=i: show_timer(i)) for i in range(3)
        ], tight=True),
        IconButton(Icons.ADD, on_click=lambda e: add_timer()),
        Text("Tip: timers run in background — switch freely.")
    ], width=drawer_width, spacing=12, alignment=MainAxisAlignment.START)

    def add_timer():
        # demo: append a new timer dynamically
        i = len(timers)
        t = CountdownTimer(page, f"Timer {i+1}", default_seconds=30)
        timers.append(t)
        # add button to drawer
        drawer.controls[1].controls.append(ElevatedButton(f"Timer {i+1}", on_click=lambda e, ii=i: show_timer(ii)))
        page.update()

    # top bar
    top_row = Row([
        Container(content=Text("Multi Countdown Timers"), alignment=alignment.center_left),
    ], alignment=MainAxisAlignment.SPACE_BETWEEN)

    # overall layout: left drawer + vertical divider + content
    layout = Row([
        Container(content=drawer, bgcolor='#F3F4F6', border=border.only(right=BorderSide(1, '#CCCCCC')), padding=10),
        Container(content=content_container, expand=True, padding=10)
    ], expand=True)

    page.add(top_row, layout)


if __name__ == "__main__":
    app(target=main)
