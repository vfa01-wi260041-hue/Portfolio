#!/usr/bin/env python3
"""
NEON BREAKOUT
=============
A small, polished brick-breaker built entirely with Tkinter — no
external packages required (Tkinter ships with standard Python on
Windows and macOS; on Linux install it via your package manager if
missing, e.g. `sudo apt install python3-tk`).

Controls:
  Mouse move   - steer the paddle
  Left / Right - steer the paddle (keyboard alternative)
  Space        - launch the ball / start / restart
  P            - pause
  Esc          - quit

Features: gradient background, glowing paddle & ball, floating score
popups, escalating levels, lives, and a high score saved to disk.
"""

import json
import math
import os
import random
import tkinter as tk
from tkinter import font as tkfont

WIDTH, HEIGHT = 820, 620
HIGH_SCORE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".neon_breakout_highscore.json")

BG_TOP = (15, 12, 41)      # #0f0c29
BG_MID = (48, 43, 99)      # #302b63
BG_BOTTOM = (36, 36, 62)   # #24243e

PADDLE_COLOR = "#00e5ff"
PADDLE_GLOW = "#0a3d4a"
BALL_COLOR = "#fff176"
BALL_GLOW = "#5c5320"

ROW_COLORS = ["#ff5e78", "#ff9d5e", "#ffd15e", "#a3ff5e", "#5ecbff", "#c05eff"]


def lerp(a, b, t):
    return a + (b - a) * t


def hex_color(rgb):
    return "#%02x%02x%02x" % tuple(max(0, min(255, int(c))) for c in rgb)


def round_rect(canvas, x1, y1, x2, y2, r=10, **kwargs):
    points = [
        x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r,
        x2, y2 - r, x2, y2, x2 - r, y2, x1 + r, y2,
        x1, y2, x1, y2 - r, x1, y1 + r, x1, y1,
    ]
    return canvas.create_polygon(points, smooth=True, **kwargs)


def load_high_score():
    try:
        with open(HIGH_SCORE_FILE) as f:
            return json.load(f).get("high_score", 0)
    except Exception:
        return 0


def save_high_score(value):
    try:
        with open(HIGH_SCORE_FILE, "w") as f:
            json.dump({"high_score": value}, f)
    except Exception:
        pass


class Popup:
    """A little floating '+10' style text that rises and fades."""

    def __init__(self, canvas, x, y, text, color):
        self.canvas = canvas
        self.life = 24
        self.max_life = 24
        self.id = canvas.create_text(
            x, y, text=text, fill=color, font=("Segoe UI", 12, "bold")
        )

    def step(self):
        self.life -= 1
        self.canvas.move(self.id, 0, -1.2)
        if self.life <= 0:
            self.canvas.delete(self.id)
            return False
        return True


class NeonBreakout:
    PADDLE_W, PADDLE_H = 110, 14
    BALL_R = 8
    ROWS, COLS = 6, 10
    BRICK_W, BRICK_H = 68, 22
    BRICK_GAP = 6
    BRICK_TOP = 90

    def __init__(self, root):
        self.root = root
        self.root.title("Neon Breakout")
        self.root.resizable(False, False)

        self.canvas = tk.Canvas(root, width=WIDTH, height=HEIGHT, highlightthickness=0, bg="#0f0c29")
        self.canvas.pack()

        self.title_font = tkfont.Font(family="Segoe UI", size=34, weight="bold")
        self.sub_font = tkfont.Font(family="Segoe UI", size=13)
        self.hud_font = tkfont.Font(family="Segoe UI", size=13, weight="bold")

        self.high_score = load_high_score()

        self.keys_left = False
        self.keys_right = False
        self.mouse_x = WIDTH / 2

        self.popups = []
        self.bg_items = []

        self.root.bind("<Motion>", self.on_mouse_move)
        self.root.bind("<Left>", lambda e: self.set_key("left", True))
        self.root.bind("<Right>", lambda e: self.set_key("right", True))
        self.root.bind("<KeyRelease-Left>", lambda e: self.set_key("left", False))
        self.root.bind("<KeyRelease-Right>", lambda e: self.set_key("right", False))
        self.root.bind("<space>", self.on_space)
        self.root.bind("<p>", self.toggle_pause)
        self.root.bind("<P>", self.toggle_pause)
        self.root.bind("<Escape>", lambda e: self.root.destroy())

        self.draw_gradient_background()
        self.state = "menu"
        self.score = 0
        self.lives = 3
        self.level = 1
        self.paused = False
        self.show_menu()
        self.loop()

    # ---------- background ----------
    def draw_gradient_background(self):
        for item in self.bg_items:
            self.canvas.delete(item)
        self.bg_items.clear()
        steps = 60
        for i in range(steps):
            t = i / steps
            if t < 0.5:
                rgb = tuple(lerp(a, b, t / 0.5) for a, b in zip(BG_TOP, BG_MID))
            else:
                rgb = tuple(lerp(a, b, (t - 0.5) / 0.5) for a, b in zip(BG_MID, BG_BOTTOM))
            y1 = int(HEIGHT * i / steps)
            y2 = int(HEIGHT * (i + 1) / steps)
            item = self.canvas.create_rectangle(0, y1, WIDTH, y2, fill=hex_color(rgb), outline="")
            self.bg_items.append(item)
        # keep background behind everything
        for item in self.bg_items:
            self.canvas.tag_lower(item)

    # ---------- input ----------
    def on_mouse_move(self, event):
        self.mouse_x = event.x

    def set_key(self, which, pressed):
        if which == "left":
            self.keys_left = pressed
        else:
            self.keys_right = pressed

    def on_space(self, event):
        if self.state == "menu":
            self.start_game()
        elif self.state == "serve":
            self.launch_ball()
        elif self.state == "gameover":
            self.start_game()

    def toggle_pause(self, event):
        if self.state == "playing":
            self.paused = not self.paused

    # ---------- screens ----------
    def clear_dynamic(self):
        self.canvas.delete("dynamic")

    def show_menu(self):
        self.clear_dynamic()
        self.canvas.create_text(
            WIDTH / 2, HEIGHT / 2 - 90, text="NEON BREAKOUT",
            font=self.title_font, fill="#ffffff", tags="dynamic"
        )
        self.canvas.create_text(
            WIDTH / 2, HEIGHT / 2 - 40,
            text="Move: mouse or arrow keys    Launch: space    Pause: P",
            font=self.sub_font, fill="#b8b8d1", tags="dynamic"
        )
        self.canvas.create_text(
            WIDTH / 2, HEIGHT / 2 + 10, text="Press SPACE to start",
            font=self.hud_font, fill=PADDLE_COLOR, tags="dynamic"
        )
        self.canvas.create_text(
            WIDTH / 2, HEIGHT / 2 + 60,
            text=f"High Score: {self.high_score}",
            font=self.sub_font, fill="#ffd15e", tags="dynamic"
        )

    def start_game(self):
        self.score = 0
        self.lives = 3
        self.level = 1
        self.state = "serve"
        self.build_level()
        self.reset_ball()

    def build_level(self):
        self.bricks = []
        total_w = self.COLS * (self.BRICK_W + self.BRICK_GAP) - self.BRICK_GAP
        start_x = (WIDTH - total_w) / 2
        for row in range(self.ROWS):
            color = ROW_COLORS[row % len(ROW_COLORS)]
            for col in range(self.COLS):
                x1 = start_x + col * (self.BRICK_W + self.BRICK_GAP)
                y1 = self.BRICK_TOP + row * (self.BRICK_H + self.BRICK_GAP)
                self.bricks.append({
                    "x1": x1, "y1": y1,
                    "x2": x1 + self.BRICK_W, "y2": y1 + self.BRICK_H,
                    "color": color, "alive": True, "id": None,
                })

    def reset_ball(self):
        self.paddle_x = WIDTH / 2
        self.ball_x = WIDTH / 2
        self.ball_y = HEIGHT - 90
        speed = 4.6 + 0.35 * (self.level - 1)
        angle = random.uniform(-0.5, 0.5)
        self.ball_vx = speed * math.sin(angle)
        self.ball_vy = -speed * math.cos(angle)
        self.state = "serve"

    def launch_ball(self):
        self.state = "playing"

    def next_level(self):
        self.level += 1
        self.build_level()
        self.reset_ball()

    def lose_life(self):
        self.lives -= 1
        if self.lives <= 0:
            self.game_over()
        else:
            self.reset_ball()

    def game_over(self):
        self.state = "gameover"
        if self.score > self.high_score:
            self.high_score = self.score
            save_high_score(self.high_score)
        self.clear_dynamic()
        self.canvas.create_text(
            WIDTH / 2, HEIGHT / 2 - 50, text="GAME OVER",
            font=self.title_font, fill="#ff5e78", tags="dynamic"
        )
        self.canvas.create_text(
            WIDTH / 2, HEIGHT / 2 + 5, text=f"Score: {self.score}    High Score: {self.high_score}",
            font=self.hud_font, fill="#ffffff", tags="dynamic"
        )
        self.canvas.create_text(
            WIDTH / 2, HEIGHT / 2 + 45, text="Press SPACE to play again",
            font=self.sub_font, fill=PADDLE_COLOR, tags="dynamic"
        )

    # ---------- physics / update ----------
    def update_paddle(self):
        target = self.mouse_x
        if self.keys_left:
            target = self.paddle_x - 12
        elif self.keys_right:
            target = self.paddle_x + 12
        self.paddle_x += (target - self.paddle_x) * 0.35
        half = self.PADDLE_W / 2
        self.paddle_x = max(half, min(WIDTH - half, self.paddle_x))
        if self.state == "serve":
            self.ball_x = self.paddle_x

    def update_ball(self):
        self.ball_x += self.ball_vx
        self.ball_y += self.ball_vy

        if self.ball_x <= self.BALL_R or self.ball_x >= WIDTH - self.BALL_R:
            self.ball_vx *= -1
            self.ball_x = max(self.BALL_R, min(WIDTH - self.BALL_R, self.ball_x))
        if self.ball_y <= self.BALL_R:
            self.ball_vy *= -1
            self.ball_y = self.BALL_R

        paddle_y = HEIGHT - 40
        half = self.PADDLE_W / 2
        if (self.ball_vy > 0 and paddle_y - self.BALL_R <= self.ball_y <= paddle_y + self.PADDLE_H
                and self.paddle_x - half <= self.ball_x <= self.paddle_x + half):
            offset = (self.ball_x - self.paddle_x) / half  # -1..1
            speed = math.hypot(self.ball_vx, self.ball_vy)
            angle = offset * 1.1
            self.ball_vx = speed * math.sin(angle)
            self.ball_vy = -abs(speed * math.cos(angle))
            self.ball_y = paddle_y - self.BALL_R

        for brick in self.bricks:
            if not brick["alive"]:
                continue
            if (brick["x1"] - self.BALL_R <= self.ball_x <= brick["x2"] + self.BALL_R
                    and brick["y1"] - self.BALL_R <= self.ball_y <= brick["y2"] + self.BALL_R):
                brick["alive"] = False
                self.ball_vy *= -1
                self.score += 10
                cx = (brick["x1"] + brick["x2"]) / 2
                cy = (brick["y1"] + brick["y2"]) / 2
                self.popups.append(Popup(self.canvas, cx, cy, "+10", brick["color"]))
                break

        if self.ball_y > HEIGHT + 20:
            self.lose_life()

        if all(not b["alive"] for b in self.bricks):
            self.next_level()

    # ---------- render ----------
    def render(self):
        self.clear_dynamic()

        # bricks
        for b in self.bricks:
            if b["alive"]:
                round_rect(self.canvas, b["x1"], b["y1"], b["x2"], b["y2"], r=6,
                           fill=b["color"], outline="", tags="dynamic")

        # paddle glow + body
        half = self.PADDLE_W / 2
        py = HEIGHT - 40
        round_rect(self.canvas, self.paddle_x - half - 4, py - 4, self.paddle_x + half + 4,
                   py + self.PADDLE_H + 4, r=10, fill=PADDLE_GLOW, outline="", tags="dynamic")
        round_rect(self.canvas, self.paddle_x - half, py, self.paddle_x + half,
                   py + self.PADDLE_H, r=7, fill=PADDLE_COLOR, outline="", tags="dynamic")

        # ball glow + body
        r = self.BALL_R
        self.canvas.create_oval(self.ball_x - r - 5, self.ball_y - r - 5,
                                 self.ball_x + r + 5, self.ball_y + r + 5,
                                 fill=BALL_GLOW, outline="", tags="dynamic")
        self.canvas.create_oval(self.ball_x - r, self.ball_y - r,
                                 self.ball_x + r, self.ball_y + r,
                                 fill=BALL_COLOR, outline="", tags="dynamic")

        # HUD
        self.canvas.create_text(60, 24, text=f"Score {self.score}", font=self.hud_font,
                                 fill="#ffffff", tags="dynamic")
        self.canvas.create_text(WIDTH / 2, 24, text=f"Level {self.level}", font=self.hud_font,
                                 fill="#b8b8d1", tags="dynamic")
        self.canvas.create_text(WIDTH - 70, 24, text="Lives " + "♥ " * self.lives, font=self.hud_font,
                                 fill="#ff5e78", tags="dynamic")

        if self.state == "serve":
            self.canvas.create_text(WIDTH / 2, HEIGHT - 120, text="Press SPACE to launch",
                                     font=self.sub_font, fill="#ffffff", tags="dynamic")

        if self.paused:
            self.canvas.create_rectangle(0, 0, WIDTH, HEIGHT, fill="#000000", stipple="gray50", tags="dynamic")
            self.canvas.create_text(WIDTH / 2, HEIGHT / 2, text="PAUSED",
                                     font=self.title_font, fill="#ffffff", tags="dynamic")

    # ---------- main loop ----------
    def loop(self):
        if self.state in ("serve", "playing") and not self.paused:
            self.update_paddle()
            if self.state == "playing":
                self.update_ball()
            self.render()

        self.popups = [p for p in self.popups if p.step()]

        self.root.after(16, self.loop)


def main():
    root = tk.Tk()
    NeonBreakout(root)
    root.mainloop()


if __name__ == "__main__":
    main()