"""حلقة اللعبة: تحديث بخطوة ثابتة، ورسم منفصل، وتتبع الاتجاهات المضغوطة."""

from __future__ import annotations

import pygame

from src.config import BG_COLOR, FPS, MAX_FRAME_TIME, MAX_STEPS_PER_FRAME, STEP
from src.core.scene_stack import SceneStack
from src.core.timing import FixedStepClock
from src.engine.input_map import DIRECTION_ACTIONS, action_for_event


class Game:
    def __init__(self, stack: SceneStack, screen: pygame.Surface) -> None:
        self.stack = stack
        self.screen = screen
        self.clock = pygame.time.Clock()
        self.timing = FixedStepClock(
            step=STEP, max_frame=MAX_FRAME_TIME, max_steps=MAX_STEPS_PER_FRAME
        )
        self.running = True
        self._held: list[str] = []

    def run(self) -> None:
        while self.running and not self.stack.is_empty:
            frame_ms = self.clock.tick(FPS)
            self._handle_events()
            self.stack.set_held(tuple(self._held))
            for _ in range(self.timing.advance(frame_ms / 1000.0)):
                if self.stack.is_empty:
                    break
                self.stack.update(STEP)
            self._draw()
            pygame.display.flip()

    def _handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return
            if event.type == pygame.WINDOWFOCUSLOST:
                self._held.clear()
            elif event.type == pygame.KEYDOWN:
                action = action_for_event(event)
                if action is None:
                    continue
                self._track_hold(action, pressed=True)
                if not self.stack.is_empty:
                    self.stack.dispatch_action(action)
            elif event.type == pygame.KEYUP:
                action = action_for_event(event)
                if action is not None:
                    self._track_hold(action, pressed=False)

    def _track_hold(self, action: str, pressed: bool) -> None:
        if action not in DIRECTION_ACTIONS:
            return
        if action in self._held:
            self._held.remove(action)
        if pressed:
            self._held.append(action)

    def _draw(self) -> None:
        self.screen.fill(BG_COLOR)
        for scene in self.stack.visible():
            scene.draw(self.screen)
