#!/usr/bin/env python3
"""Render the news-image-20261126 entry image (1024x1024 PNG).

Draws a one-day newspaper front page for Thursday 26 November 2026 with
Pillow (local build tool only; the entry program main.ts just copies the
rendered entry.png). Deterministic: same input always yields the same bytes.

Stories were verified against Reuters/AP/FIDE/BEA reporting of 25-26 Nov 2026
(see SOURCES.md). Nothing here is invented: every headline below is a
reported fact of the day's news cycle.
"""
import argparse
import os
import sys

from PIL import Image, ImageDraw, ImageFont

W, H = 1024, 1024
PAPER = (248, 244, 236)
INK = (20, 20, 20)
RED = (176, 30, 36)
BLUE = (31, 78, 121)
TEAL = (14, 110, 110)
GREY = (90, 88, 82)
LIGHT = (233, 228, 218)
SKY = (178, 214, 235)

SERIF_B = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
SERIF = "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"
SANS_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"


def font(path, size):
    return ImageFont.truetype(path, size)


def wrap(draw, text, fnt, max_w):
    words, lines, cur = text.split(), [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if draw.textlength(trial, font=fnt) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def draw_text_block(draw, x, y, lines, fnt, fill, leading):
    for line in lines:
        draw.text((x, y), line, font=fnt, fill=fill)
        y += leading
    return y


def hline(draw, x0, x1, y, fill=INK, width=2):
    draw.line([(x0, y), (x1, y)], fill=fill, width=width)


# ---- small pictograms, drawn with primitives only -----------------------
def icon_balloon(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=SKY)
    d.ellipse([x + 8, y + 58, x + 52, y + 78], fill=(255, 255, 255))
    d.ellipse([x + w - 60, y + 78, x + w - 16, y + 96], fill=(255, 255, 255))
    d.ellipse([x + w // 2 - 34, y + 8, x + w // 2 + 34, y + 78], fill=RED)
    d.ellipse([x + w // 2 - 26, y + 16, x + w // 2 - 6, y + 58], fill=(215, 90, 90))
    d.line([(x + w // 2 - 18, y + 76), (x + w // 2 - 8, y + 104)], fill=INK, width=2)
    d.line([(x + w // 2 + 18, y + 76), (x + w // 2 + 8, y + 104)], fill=INK, width=2)
    d.rectangle([x + w // 2 - 10, y + 104, x + w // 2 + 10, y + 120], fill=(120, 72, 20))
    d.rectangle([x, y + h - 14, x + w, y + h], fill=(60, 60, 60))


def icon_chart(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(232, 240, 232))
    bars = [(18, 30), (48, 42), (78, 56)]
    for bx, bh in bars:
        d.rectangle([x + bx, y + h - 22 - bh, x + bx + 22, y + h - 22], fill=TEAL)
    d.line([(x + 10, y + h - 22), (x + w - 8, y + h - 22)], fill=INK, width=3)
    d.line([(x + 10, y + 12), (x + 10, y + h - 22)], fill=INK, width=3)
    d.text((x + 58, y + 4), "4.3%", font=font(SANS_B, 20), fill=RED)


def icon_trade(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(226, 234, 244))
    cx, cy, r = x + w // 2, y + h // 2 + 6, 42
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(90, 150, 200))
    d.ellipse([cx - 26, cy - 30, cx - 2, cy - 6], fill=(90, 170, 90))
    d.ellipse([cx + 2, cy + 8, cx + 28, cy + 30], fill=(90, 170, 90))
    d.line([(cx - 52, cy - 44), (cx + 52, cy - 44)], fill=RED, width=4)
    d.polygon([(cx + 52, cy - 52), (cx + 52, cy - 36), (cx + 64, cy - 44)], fill=RED)


def icon_barrel(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(245, 232, 210))
    d.ellipse([x + 22, y + 14, x + w - 22, y + 58], fill=(255, 120, 30))
    d.polygon([(x + w // 2, y + 2), (x + w // 2 - 12, y + 26),
               (x + w // 2 + 12, y + 26)], fill=(255, 60, 20))
    d.rounded_rectangle([x + 28, y + 56, x + w - 28, y + h - 16], radius=8, fill=(40, 40, 40))
    d.line([(x + 28, y + 72), (x + w - 28, y + 72)], fill=(120, 120, 120), width=2)
    d.line([(x + 28, y + 92), (x + w - 28, y + 92)], fill=(120, 120, 120), width=2)


def icon_flame(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(40, 32, 28))
    d.polygon([(x + w // 2, y + 12), (x + w - 18, y + 70), (x + w // 2 + 14, y + 62),
               (x + w // 2 - 6, y + 88), (x + 18, y + 70)], fill=(255, 110, 20))
    d.polygon([(x + w // 2, y + 48), (x + w - 30, y + 88), (x + 30, y + 88)], fill=(255, 200, 40))
    d.rectangle([x + 16, y + h - 24, x + w - 16, y + h - 8], fill=(90, 90, 90))
    d.text((x + w // 2 - 8, y + h - 23), "31", font=font(SANS_B, 14), fill=(255, 255, 255))


def icon_drone(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(226, 228, 232))
    cx, cy = x + w // 2, y + h // 2
    d.ellipse([cx - 26, cy - 12, cx + 26, cy + 12], fill=(70, 70, 70))
    d.ellipse([cx - 8, cy - 5, cx + 8, cy + 5], fill=RED)
    for sx in (-38, 38):
        d.line([(cx + sx, cy - 22), (cx + sx, cy - 6)], fill=INK, width=2)
        d.ellipse([cx + sx - 16, cy - 26, cx + sx + 16, cy - 18], fill=(150, 150, 150))
    d.line([(cx - 22, cy + 12), (cx - 34, cy + 30)], fill=INK, width=2)
    d.line([(cx + 22, cy + 12), (cx + 34, cy + 30)], fill=INK, width=2)


def icon_candle(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(30, 44, 66))
    d.rectangle([x + w // 2 - 14, y + 44, x + w // 2 + 14, y + h - 20], fill=(245, 240, 225))
    d.ellipse([x + w // 2 - 8, y + 18, x + w // 2 + 8, y + 42], fill=(255, 200, 60))
    d.rectangle([x + w // 2 - 26, y + h - 20, x + w // 2 + 26, y + h - 12], fill=(180, 170, 150))
    d.text((x + 14, y + 6), "26/11", font=font(SANS_B, 20), fill=(255, 255, 255))


def icon_chess(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(240, 230, 210))
    sq = 26
    ox, oy = x + 10, y + 12
    for r in range(4):
        for c in range(4):
            if (r + c) % 2 == 0:
                d.rectangle([ox + c * sq, oy + r * sq,
                             ox + (c + 1) * sq, oy + (r + 1) * sq], fill=(60, 60, 60))
    d.text((ox + 6, oy + 30), "\u265e", font=font(SANS, 52), fill=(255, 255, 255))


ICONS = {
    "balloon": icon_balloon, "chart": icon_chart, "trade": icon_trade,
    "barrel": icon_barrel, "flame": icon_flame, "drone": icon_drone,
    "candle": icon_candle, "chess": icon_chess,
}

CARDS = [
    ("chart", "ECONOMY · USA", "US economy grows 4.3%",
     "Q3 growth revised sharply up; inflation hits 3.8%, a three-year high."),
    ("trade", "TRADE · WORLD", "Trump tariffs hit 14 economies",
     "New duties proposed for China, the EU, Japan and more."),
    ("barrel", "ENERGY · MIDDLE EAST", "Brent jumps to $94.61 a barrel",
     "Houthis claim a hit on Saudi Arabia's Ras Tanura refinery."),
    ("flame", "EGYPT · DISASTER", "Cairo tanker fire kills 31",
     "Fuel tanker crash sets the Ring Road ablaze; 21 hurt."),
    ("drone", "SUDAN · CONFLICT", "Drones kill 19 in Blue Nile",
     "Strikes hit homes in Damazin, a rights group says."),
    ("candle", "INDIA · REMEMBRANCE", "Mumbai marks 18 years since 26/11",
     "166 victims remembered at tributes across the city."),
]

BRIEFS = [
    ("GAZA", "Israeli strike kills a Hamas official and his family in Shati camp."),
    ("BANGLADESH", "Garment workers win a 36% pay rise, to 17,000 taka a month."),
    ("CHESS", "Gukesh v Sindarov, Game 3 in Geneva; the match is level at 1-1."),
    ("NORTH KOREA", "Kim orders wider deployment of tactical nuclear arms."),
    ("UKRAINE", "Kyiv says it struck a Russian air base, damaging five planes."),
    ("LEBANON", "A second airport is planned for the north, at Kleiat."),
    ("USA", "A second judge blocks Trump's birthright citizenship order."),
    ("THANKSGIVING", "US markets closed for the holiday as a storm hits the East Coast."),
]


def render(out_path):
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)

    # masthead
    d.rectangle([0, 0, W, 6], fill=RED)
    kicker = font(SANS_B, 15)
    txt = "ONE DAY  ·  EVERY REGION  ·  EVERY FIELD"
    d.text(((W - d.textlength(txt, font=kicker)) / 2, 16), txt, font=kicker, fill=GREY)
    title = font(SERIF_B, 62)
    t = "THE WORLD IN ONE DAY"
    d.text(((W - d.textlength(t, font=title)) / 2, 38), t, font=title, fill=INK)
    # date band
    d.rectangle([24, 112, W - 24, 152], fill=RED)
    date_f = font(SANS_B, 30)
    d.text((44, 118), "THURSDAY 26 NOVEMBER 2026", font=date_f, fill=(255, 255, 255))
    sub_f = font(SANS_B, 18)
    s = "15 STORIES · 6 REGIONS"
    d.text((W - 44 - d.textlength(s, font=sub_f), 124), s, font=sub_f, fill=(255, 255, 255))
    hline(d, 24, W - 24, 162, width=2)

    # lead story
    ly = 176
    ICONS["balloon"](d, 24, ly, 300, 168)
    d.text((344, ly), "NEW YORK · THANKSGIVING", font=font(SANS_B, 15), fill=RED)
    head_f = font(SERIF_B, 33)
    lines = wrap(d, "100th Macy's parade postponed — a first in 100 years",
                 head_f, 640)
    y = draw_text_block(d, 344, ly + 24, lines, head_f, INK, 40)
    deck = wrap(d, "A storm grounds the giant balloons. The Thanksgiving parade "
                   "moves to Saturday 28 Nov, stepping off at 8:30 a.m.",
                font(SANS, 18), 640)
    draw_text_block(d, 344, y + 6, deck, font(SANS, 18), (60, 58, 52), 24)
    hline(d, 24, W - 24, ly + 180, width=2)

    # six story cards, 2 columns x 3 rows
    gy, ch, gap = 368, 118, 10
    cw = (W - 48 - gap) // 2
    for i, (icon, kick, head, deck_txt) in enumerate(CARDS):
        cx = 24 + (i % 2) * (cw + gap)
        cy = gy + (i // 2) * (ch + gap)
        d.rectangle([cx, cy, cx + cw, cy + ch], outline=(200, 194, 182), width=1)
        ICONS[icon](d, cx + 8, cy + 8, 112, ch - 16)
        tx = cx + 132
        d.text((tx, cy + 10), kick, font=font(SANS_B, 13), fill=RED)
        hf = font(SERIF_B, 21)
        hl = wrap(d, head, hf, cw - 144)
        yy = draw_text_block(d, tx, cy + 32, hl[:2], hf, INK, 26)
        df = font(SANS, 15)
        dl = wrap(d, deck_txt, df, cw - 144)
        draw_text_block(d, tx, yy + 4, dl[:2], df, (60, 58, 52), 19)

    # also-today briefs
    by = gy + 3 * ch + 2 * gap + 14
    d.rectangle([24, by, W - 24, by + 30], fill=INK)
    d.text((36, by + 4), "ALSO TODAY", font=font(SANS_B, 17), fill=(255, 255, 255))
    bf = font(SANS, 16)
    bfb = font(SANS_B, 16)
    yy = by + 42
    for region, text in BRIEFS:
        d.text((36, yy), region + " — ", font=bfb, fill=INK)
        off = d.textlength(region + " — ", font=bfb)
        d.text((36 + off, yy), text, font=bf, fill=(40, 38, 34))
        yy += 23

    # footer
    fy = yy + 8
    hline(d, 24, W - 24, fy, width=2)
    ff = font(SANS, 13)
    ft = ("Sources: Reuters · AP · FIDE · US Bureau of Economic Analysis — "
          "events as reported around the world on 26 November 2026.")
    d.text(((W - d.textlength(ft, font=ff)) / 2, fy + 10), ft, font=ff, fill=GREY)

    img.save(out_path, format="PNG")
    print(f"wrote {out_path} {os.path.getsize(out_path)} bytes")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="entry.png")
    args = ap.parse_args()
    render(args.out)
