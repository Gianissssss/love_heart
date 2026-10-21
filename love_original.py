import math as m
import random as r
import turtle as t
import tkinter.font as tkf

SC = 21
OY = 20
DURATION = 10
TICK = 16
ANIM = 42
LIFT = 34
GAP = 7
SIZES = (9, 10, 11, 12)
FONT = "Arial"
BG = "#060208"

s = t.Screen()
s.setup(800, 800)
s.bgcolor(BG)
s.title("Love Heart")
s.tracer(0)

cv = s.getcanvas()
rng = r.Random(11)

PHRASES = [
    "I love you", "Seni seviyorum", "Te amo", "Je t'aime",
    "Ich liebe dich", "Ti amo", "Eu te amo", "Я тебя люблю",
    "사랑해", "愛してる", "我爱你", "मैं तुमसे प्यार करता हूँ",
    "Σ' αγαπώ", "Ik hou van jou", "Jag älskar dig", "Kocham cię",
    "ฉันรักเธอ", "Anh yêu em", "Aku cinta kamu", "Я тебе кохаю",
]

_fonts = {}


def font_for(size):
    if size not in _fonts:
        _fonts[size] = tkf.Font(
            root=cv, family=FONT, size=size, weight="bold"
        )
    return _fonts[size]


def heart(a):
    x = 16 * (m.sin(a) ** 3)
    y = (
        13 * m.cos(a)
        - 5 * m.cos(2 * a)
        - 2 * m.cos(3 * a)
        - m.cos(4 * a)
    )
    return x * SC, y * SC + OY


def hx(c):
    return "#%02x%02x%02x" % tuple(
        int(max(0, min(1, v)) * 255) for v in c
    )


def mix(a, b, k):
    return tuple(p + (q - p) * k for p, q in zip(a, b))


def dim(c, k):
    return tuple(v * k for v in c)


POLY = [heart(2 * m.pi * i / 720) for i in range(720)]
EDGES = list(zip(POLY, POLY[1:] + POLY[:1]))
YMAX = max(p[1] for p in POLY)
YMIN = min(p[1] for p in POLY)
CY = (YMAX + YMIN) / 2


def spans(y):
    xs = []
    for (x1, y1), (x2, y2) in EDGES:
        if (y1 <= y < y2) or (y2 <= y < y1):
            xs.append(x1 + (y - y1) * (x2 - x1) / (y2 - y1))
    xs.sort()
    return list(zip(xs[0::2], xs[1::2]))


def intersect(A, B):
    out = []
    for a in A:
        for b in B:
            lo, hi = max(a[0], b[0]), min(a[1], b[1])
            if hi - lo > 14:
                out.append((lo, hi))
    return out


def phrase_cycle():
    while True:
        order = PHRASES[:]
        rng.shuffle(order)
        yield from order


def build():
    cycle = phrase_cycle()
    row_h = max(font_for(z).metrics("linespace") for z in SIZES) + 4
    half = row_h / 2
    placed = []

    y = YMAX - half
    while y > YMIN + half:
        row = intersect(spans(y + half), spans(y - half))

        for lo, hi in row:
            lo += 4
            hi -= 4
            cur = lo + rng.uniform(0, 8)
            line = []

            while True:
                fit = None
                for _ in range(10):
                    text = next(cycle)
                    size = rng.choice(SIZES)
                    w = font_for(size).measure(text)
                    if cur + w <= hi:
                        fit = (text, size, w)
                        break
                if not fit:
                    break
                text, size, w = fit
                line.append([cur + w / 2, text, size, w])
                cur += w + GAP

            if not line:
                continue

            if len(line) > 1:
                left = hi - (line[-1][0] + line[-1][3] / 2)
                for i, it in enumerate(line):
                    it[0] += left * i / (len(line) - 1)
            else:
                line[0][0] = (lo + hi) / 2

            for i, (x, text, size, w) in enumerate(line):
                edge = i == 0 or i == len(line) - 1
                placed.append(dict(x=x, y=y, text=text, size=size, edge=edge))

        y -= row_h

    wine = (0.58, 0.0, 0.09)
    crimson = (0.90, 0.05, 0.14)
    blood = (0.98, 0.10, 0.16)
   # Paleta: carmesí, rosa, violeta y azul
    wine = (0.24, 0.015, 0.20)
    crimson = (0.82, 0.025, 0.16)
    rose = (1.00, 0.18, 0.42)
    violet = (0.48, 0.16, 0.88)
    blue = (0.12, 0.48, 1.00)

    for p in placed:
        rad = min(1.0, math_dist(p["x"], p["y"]))

        # Base roja: tonos más intensos hacia el exterior
        base = mix(wine, crimson, 0.30 + 0.70 * rad)

        # Reflejos violetas y azules distribuidos alrededor del corazón
        angle = (
            m.atan2(p["y"] - CY, p["x"]) + m.pi
        ) / (2 * m.pi)
        wave = (m.sin(angle * 2 * m.pi) + 1) / 2
        accent = mix(violet, blue, wave)
        base = mix(base, accent, 0.13)

        # Bordes rosados para definir la silueta
        if p["edge"]:
            base = mix(base, rose, 0.24)

        p["color"] = tuple(
            max(0.0, min(1.0, v))
            for v in base
        )
        p["rad"] = rad

    edges = [p for p in placed if p["edge"]]
    inner = [p for p in placed if not p["edge"]]
    edges.sort(key=lambda p: m.atan2(p["x"], p["y"] - CY) % (2 * m.pi))
    inner.sort(key=lambda p: -p["rad"] + rng.uniform(0, 0.08))
    return edges + inner


def math_dist(x, y):
    return m.hypot(x / (16 * SC), (y - CY) / (14.5 * SC))


FLASH = (1.0, 0.84, 0.94)
main_ids = []
active = []
pulse_items = []
pulse_phase = 0.0
tick_no = 0


def clamp(v):
    return max(0.0, min(1.0, v))


def spawn(p):
    x, y = p["x"], -p["y"]
    size, text, c = p["size"], p["text"], p["color"]
    font = (FONT, size, "bold")
    big = (FONT, size + 3, "bold")

    shadow = cv.create_text(x + 2, y + 3, text=text, font=font, fill=BG)
    halo = cv.create_text(x, y, text=text, font=big, fill=BG)
    main = cv.create_text(x, y - LIFT, text=text, font=font, fill=BG)

    p.update(shadow=shadow, halo=halo, main=main,
             f=0, dx=rng.uniform(-10, 10))
    main_ids.append((main, c))
    pulse_items.append((main, size, x,y,halo, shadow))
    active.append(p)


def animate(p):
    p["f"] += 1
    u = clamp(p["f"] / ANIM)
    e = 1 - (1 - u) ** 3
    c = p["color"]
    x, y = p["x"], -p["y"]
    hover = (1 - e) * LIFT
    px = x + p["dx"] * (1 - e)
    py = y - hover

    cv.itemconfig(p["shadow"], fill=hx(mix(BGC, dim(c, 0.30), e)))
    cv.itemconfig(p["halo"], fill=hx(mix(BGC, dim(c, 0.40), e * e)))
    cv.coords(p["halo"], px, py)

    flash = 0.75 * math_sin(clamp((u - 0.55) / 0.45))
    col = mix(mix(BGC, c, e ** 1.5), FLASH, flash)
    cv.itemconfig(p["main"], fill=hx(col))
    cv.coords(p["main"], px, py)

    if u >= 1:
        cv.coords(p["halo"], x, y)
        cv.coords(p["main"], x, y)
        cv.itemconfig(p["main"], fill=hx(c))
        return False
    return True


def math_sin(v):
    return m.sin(m.pi * v)


BGC = tuple(int(BG[i:i + 2], 16) / 255 for i in (1, 3, 5))
ORDER = build()
items = iter(ORDER)
RATE = len(ORDER) / (DURATION * 1000 / TICK)
acc = 0.0
spawning = True


def step():
    global spawning, acc
    if spawning:
        acc += RATE
        try:
            while acc >= 1:
                acc -= 1
                spawn(next(items))
        except StopIteration:
            spawning = False

    active[:] = [p for p in active if animate(p)]

    if not spawning and not active:
        shimmer()
        return
    cv.after(TICK, step)


def _safe(i, c):
    try:
        cv.itemconfig(i, fill=hx(c))
    except Exception:
        pass


SHIMMER_COLORS = [
    (1.0, 0.72, 0.88),   # Rosa
    (0.72, 0.48, 1.0),   # Violeta
    (0.42, 0.72, 1.0),   # Azul
    (1.0, 0.84, 0.94),   # Rosa claro
]

def shimmer():
    global pulse_phase

    if not main_ids:
        cv.after(160, shimmer)
        return

    # 1. Destellos de colores sobre distintas frases
    chosen = rng.sample(main_ids, k=min(3, len(main_ids)))

    for i, c in chosen:
        glow = rng.choice(SHIMMER_COLORS)
        _safe(i, mix(c, glow, 0.78))
        cv.after(
            300,
            lambda i=i, c=c: _safe(i, c)
        )

    # 2. Estrellitas que aparecen y desaparecen
    for _ in range(2):
        i, c = rng.choice(main_ids)
        pos = cv.coords(i)

        if len(pos) >= 2:
            x, y = pos[0], pos[1]
            x += rng.uniform(-18, 18)
            y += rng.uniform(-14, 14)

            star = cv.create_text(
                x, y,
                text=rng.choice(["✦", "✧", "⋆"]),
                font=("Segoe UI Symbol", rng.choice([9, 11, 13])),
                fill=hx(rng.choice(SHIMMER_COLORS))
            )

            cv.after(500, lambda star=star: cv.delete(star))

    # 3. Latido de toda la silueta
    pulse_phase += 0.22
    beat = max(0, m.sin(pulse_phase))
    scale = 1 + 0.025 * beat

    for item, original_size, x, y, halo, shadow in pulse_items:
        try:
            cv.coords(main_id := item, x * scale, y * scale)
            cv.coords(halo, x * scale, y * scale)
            cv.coords(shadow, x * scale + 2, y * scale + 3)

            size = original_size + (1 if beat > 0.7 else 0)
            cv.itemconfig(item, font=(FONT, size, "bold"))
            cv.itemconfig(halo, font=(FONT, size + 3, "bold"))
        except Exception:
            pass

    cv.after(220, shimmer)

BG_STARS = []

def init_background():
    # Estrellas discretas distribuidas por el fondo
    for _ in range(85):
        x = rng.uniform(-380, 380)
        y = rng.uniform(-380, 380)

        star = cv.create_text(
            x, y,
            text=rng.choice(["·", "✦", "✧", "⋆"]),
            font=("Arial", rng.choice([6, 8, 10])),
            fill=rng.choice(["#49305f", "#354d83", "#8060a8"])
        )

        BG_STARS.append({
            "id": star,
            "x": x,
            "y": y,
            "phase": rng.uniform(0, 6.28),
            "speed": rng.uniform(0.01, 0.04)
        })

    # Firma debajo del corazón
    cv.create_text(
        0, 365,
        text="Te amo ♡",
        font=("Arial", 17, "bold"),
        fill="#dba4ff"
    )


def animate_background():
    for star in BG_STARS:
        star["phase"] += star["speed"]

        brightness = (m.sin(star["phase"]) + 1) / 2
        colors = ["#49305f", "#8060a8", "#c5a3ff"]
        index = int(brightness * (len(colors) - 1))

        _safe(star["id"], tuple(
            int(colors[index][i:i+2], 16) / 255
            for i in (1, 3, 5)
        ))

        # Movimiento muy suave
        star["y"] += 0.12
        if star["y"] > 400:
            star["y"] = -400

        cv.coords(star["id"], star["x"], star["y"])

    cv.tag_lower("background")
    cv.after(70, animate_background)

try:
    init_background()
    cv.after(70, animate_background)
    cv.after(200, step)
    t.done()
except (t.Terminator, Exception):
    pass