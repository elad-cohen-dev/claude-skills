"""Worked example: an architecture view and a sequence diagram with an alt block.

    python3 example.py      # writes architecture.excalidraw and checkout.excalidraw to the cwd
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "scripts"))
from excal_lib import (BLUE, GREEN, ORANGE, PURPLE, S_BLUE, S_GREEN, S_GREY, S_ORANGE, S_PURPLE,
                       S_TEAL, TEAL, Scene, lifelines, msg)


def architecture():
    s = Scene()
    s.text("title", 40, 0, "Orders — architecture", 28)
    s.zone("zfe", 20, 60, 340, 400, "web app", "#dbe4ff", S_BLUE, S_BLUE)
    s.box("cart", 45, 130, 290, 90, "Cart page", BLUE)
    s.box("hist", 45, 290, 290, 90, "Order history", BLUE)
    s.zone("zapi", 420, 60, 380, 400, "orders-api", "#d3f9d8", S_GREEN, S_GREEN)
    s.box("rt", 445, 130, 330, 90, "routers\nauth + validation", GREEN)
    s.box("svc", 445, 290, 330, 90, "OrderService\nplace · list", GREEN)
    s.box("db", 880, 130, 280, 90, "PostgreSQL\norders", TEAL)
    s.box("pay", 880, 290, 280, 90, "Payment provider", ORANGE)
    s.arrow("a1", [(335, 175), (445, 175)], "cart", "rt", label="POST /orders")
    s.arrow("a2", [(335, 335), (380, 335), (380, 200), (445, 200)], "hist", "rt", label="GET /orders",
            label_at=(318, 262))
    s.arrow("a3", [(610, 220), (610, 290)], "rt", "svc")
    s.arrow("a4", [(775, 310), (830, 310), (830, 175), (880, 175)], "svc", "db", label="insert / select",
            label_at=(830, 150))
    s.arrow("a5", [(775, 350), (880, 350)], "svc", "pay", stroke=S_ORANGE, style="dashed", label="charge",
            label_at=(828, 358))
    s.save("architecture")


def checkout():
    s = Scene()
    WEB, API, PAY, DB = 150, 560, 970, 1380
    s.text("title", 40, 0, "Checkout", 28)
    lifelines(s, [("web", WEB, "web app", BLUE, S_BLUE), ("api", API, "orders-api", GREEN, S_GREEN),
                  ("pay", PAY, "payment provider", ORANGE, S_ORANGE), ("db", DB, "PostgreSQL", TEAL, S_TEAL)],
              60, 640)
    msg(s, "m1", WEB, API, 170, "POST /orders { cart_id }", S_BLUE)
    msg(s, "m2", API, API, 210, "validate cart", S_GREEN)
    msg(s, "m3", API, PAY, 300, "charge(amount)", S_GREEN)
    ay = 330
    s.box("alt", API - 110, ay, (DB - API) + 230, 200, None, "transparent", stroke=S_GREY, style="dashed", sw=1)
    s.text("alt_l", API - 100, ay + 6, "alt", 16, color=S_GREY)
    s.text("alt_c1", API - 60, ay + 6, "[declined] → 402 to the client", 14, color="#e03131")
    s.arrow("sep", [(API - 110, ay + 40), (DB + 120, ay + 40)], stroke=S_GREY, style="dashed", head=None, sw=1)
    s.text("alt_c2", API - 60, ay + 48, "[approved]", 14, color=S_GREY)
    msg(s, "m4", API, DB, ay + 120, "insert order (paid)", S_GREEN)
    msg(s, "m5", API, WEB, ay + 180, "201 { order_id }", S_GREEN, "dashed")
    s.save("checkout")


if __name__ == "__main__":
    architecture()
    checkout()
