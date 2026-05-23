from flask import Flask, request, jsonify, send_from_directory, session
from flask_cors import CORS
import os, hashlib, datetime, pytz
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__, static_folder="static")
app.secret_key = os.environ.get("SECRET_KEY", "wc2026-tajny-klic-xk29")
CORS(app, supports_credentials=True)

DATABASE_URL = os.environ.get("DATABASE_URL")
ADMIN = "Admin"
CEST  = pytz.timezone("Europe/Prague")

# ── ZÁPASY — časy v CEST (převedeno z GMT/UTC dle FIFA rozpisu) ──────────────
# Skupiny dle FIFA: A=Mexico/RSA/KOR/CZE, B=Canada/BIH/QAT/SUI,
# C=BRA/MAR/HAI/SCO, D=USA/PAR/AUS/TUR, E=GER/CUW/CIV/ECU,
# F=NED/JPN/SWE/TUN, G=BEL/EGY/IRN/NZL, H=ESP/CPV/KSA/URU,
# I=FRA/SEN/IRQ/NOR, J=ARG/ALG/AUT/JOR, K=POR/COD/UZB/COL, L=ENG/CRO/GHA/PAN

GAMES = [
    {"id":"m1",  "date":"2026-06-11","time":"21:00","home":"Mexiko",              "away":"Jižní Afrika",       "group":"A"},
    {"id":"m2",  "date":"2026-06-12","time":"04:00","home":"Jižní Korea",         "away":"Česká rep.",         "group":"A"},
    {"id":"m3",  "date":"2026-06-12","time":"21:00","home":"Kanada",              "away":"Bosna a Herceg.",    "group":"B"},
    {"id":"m4",  "date":"2026-06-13","time":"03:00","home":"USA",                 "away":"Paraguay",           "group":"D"},
    {"id":"m5",  "date":"2026-06-14","time":"03:00","home":"Haiti",               "away":"Skotsko",            "group":"C"},
    {"id":"m6",  "date":"2026-06-14","time":"06:00","home":"Austrálie",           "away":"Turecko",            "group":"D"},
    {"id":"m7",  "date":"2026-06-14","time":"00:00","home":"Brazílie",            "away":"Maroko",             "group":"C"},
    {"id":"m8",  "date":"2026-06-13","time":"21:00","home":"Katar",               "away":"Švýcarsko",          "group":"B"},
    {"id":"m9",  "date":"2026-06-15","time":"01:00","home":"Pobřeží slonoviny",   "away":"Ekvádor",            "group":"E"},
    {"id":"m10", "date":"2026-06-14","time":"19:00","home":"Německo",             "away":"Curaçao",            "group":"E"},
    {"id":"m11", "date":"2026-06-14","time":"22:00","home":"Nizozemsko",          "away":"Japonsko",           "group":"F"},
    {"id":"m12", "date":"2026-06-15","time":"04:00","home":"Švédsko",             "away":"Tunisko",            "group":"F"},
    {"id":"m13", "date":"2026-06-16","time":"00:00","home":"Saúdská Arábie",      "away":"Uruguay",            "group":"H"},
    {"id":"m14", "date":"2026-06-15","time":"18:00","home":"Španělsko",           "away":"Kapverdy",           "group":"H"},
    {"id":"m15", "date":"2026-06-16","time":"03:00","home":"Írán",                "away":"Nový Zéland",        "group":"G"},
    {"id":"m16", "date":"2026-06-15","time":"21:00","home":"Belgie",              "away":"Egypt",              "group":"G"},
    {"id":"m17", "date":"2026-06-16","time":"21:00","home":"Francie",             "away":"Senegal",            "group":"I"},
    {"id":"m18", "date":"2026-06-17","time":"00:00","home":"Irák",                "away":"Norsko",             "group":"I"},
    {"id":"m19", "date":"2026-06-17","time":"03:00","home":"Argentina",           "away":"Alžírsko",           "group":"J"},
    {"id":"m20", "date":"2026-06-17","time":"06:00","home":"Rakousko",            "away":"Jordánsko",          "group":"J"},
    {"id":"m21", "date":"2026-06-18","time":"01:00","home":"Ghana",               "away":"Panama",             "group":"L"},
    {"id":"m22", "date":"2026-06-17","time":"22:00","home":"Anglie",              "away":"Chorvatsko",         "group":"L"},
    {"id":"m23", "date":"2026-06-17","time":"19:00","home":"Portugalsko",         "away":"DR Kongo",           "group":"K"},
    {"id":"m24", "date":"2026-06-18","time":"04:00","home":"Uzbekistán",          "away":"Kolumbie",           "group":"K"},
    {"id":"m25", "date":"2026-06-18","time":"18:00","home":"Česká rep.",          "away":"Jižní Afrika",       "group":"A"},
    {"id":"m26", "date":"2026-06-18","time":"21:00","home":"Švýcarsko",           "away":"Bosna a Herceg.",    "group":"B"},
    {"id":"m27", "date":"2026-06-19","time":"00:00","home":"Kanada",              "away":"Katar",              "group":"B"},
    {"id":"m28", "date":"2026-06-19","time":"03:00","home":"Mexiko",              "away":"Jižní Korea",        "group":"A"},
    {"id":"m29", "date":"2026-06-20","time":"02:30","home":"Brazílie",            "away":"Haiti",              "group":"C"},
    {"id":"m30", "date":"2026-06-20","time":"00:00","home":"Skotsko",             "away":"Maroko",             "group":"C"},
    {"id":"m31", "date":"2026-06-20","time":"05:00","home":"USA",                 "away":"Austrálie",          "group":"D"},
    {"id":"m32", "date":"2026-06-19","time":"21:00","home":"Turecko",             "away":"Paraguay",           "group":"D"},
    {"id":"m33", "date":"2026-06-20","time":"22:00","home":"Německo",             "away":"Pobřeží slonoviny",  "group":"E"},
    {"id":"m34", "date":"2026-06-21","time":"02:00","home":"Ekvádor",             "away":"Curaçao",            "group":"E"},
    {"id":"m35", "date":"2026-06-20","time":"19:00","home":"Nizozemsko",          "away":"Švédsko",            "group":"F"},
    {"id":"m36", "date":"2026-06-21","time":"06:00","home":"Tunisko",             "away":"Japonsko",           "group":"F"},
    {"id":"m37", "date":"2026-06-22","time":"00:00","home":"Uruguay",             "away":"Kapverdy",           "group":"H"},
    {"id":"m38", "date":"2026-06-21","time":"18:00","home":"Španělsko",           "away":"Saúdská Arábie",     "group":"H"},
    {"id":"m39", "date":"2026-06-21","time":"21:00","home":"Belgie",              "away":"Írán",               "group":"G"},
    {"id":"m40", "date":"2026-06-22","time":"03:00","home":"Nový Zéland",         "away":"Egypt",              "group":"G"},
    {"id":"m41", "date":"2026-06-23","time":"02:00","home":"Norsko",              "away":"Senegal",            "group":"I"},
    {"id":"m42", "date":"2026-06-22","time":"22:00","home":"Francie",             "away":"Irák",               "group":"I"},
    {"id":"m43", "date":"2026-06-22","time":"19:00","home":"Argentina",           "away":"Rakousko",           "group":"J"},
    {"id":"m44", "date":"2026-06-23","time":"05:00","home":"Jordánsko",           "away":"Alžírsko",           "group":"J"},
    {"id":"m45", "date":"2026-06-23","time":"22:00","home":"Anglie",              "away":"Ghana",              "group":"L"},
    {"id":"m46", "date":"2026-06-24","time":"01:00","home":"Panama",              "away":"Chorvatsko",         "group":"L"},
    {"id":"m47", "date":"2026-06-23","time":"19:00","home":"Portugalsko",         "away":"Uzbekistán",         "group":"K"},
    {"id":"m48", "date":"2026-06-24","time":"04:00","home":"Kolumbie",            "away":"DR Kongo",           "group":"K"},
    {"id":"m49", "date":"2026-06-25","time":"00:00","home":"Skotsko",             "away":"Brazílie",           "group":"C"},
    {"id":"m50", "date":"2026-06-25","time":"00:00","home":"Maroko",              "away":"Haiti",              "group":"C"},
    {"id":"m51", "date":"2026-06-24","time":"21:00","home":"Švýcarsko",           "away":"Kanada",             "group":"B"},
    {"id":"m52", "date":"2026-06-24","time":"21:00","home":"Bosna a Herceg.",     "away":"Katar",              "group":"B"},
    {"id":"m53", "date":"2026-06-25","time":"03:00","home":"Česká rep.",          "away":"Mexiko",             "group":"A"},
    {"id":"m54", "date":"2026-06-25","time":"03:00","home":"Jižní Afrika",        "away":"Jižní Korea",        "group":"A"},
    {"id":"m55", "date":"2026-06-25","time":"22:00","home":"Curaçao",             "away":"Pobřeží slonoviny",  "group":"E"},
    {"id":"m56", "date":"2026-06-25","time":"22:00","home":"Ekvádor",             "away":"Německo",            "group":"E"},
    {"id":"m57", "date":"2026-06-26","time":"01:00","home":"Japonsko",            "away":"Švédsko",            "group":"F"},
    {"id":"m58", "date":"2026-06-26","time":"01:00","home":"Tunisko",             "away":"Nizozemsko",         "group":"F"},
    {"id":"m59", "date":"2026-06-26","time":"04:00","home":"Turecko",             "away":"USA",                "group":"D"},
    {"id":"m60", "date":"2026-06-26","time":"04:00","home":"Paraguay",            "away":"Austrálie",          "group":"D"},
    {"id":"m61", "date":"2026-06-26","time":"21:00","home":"Norsko",              "away":"Francie",            "group":"I"},
    {"id":"m62", "date":"2026-06-26","time":"21:00","home":"Senegal",             "away":"Irák",               "group":"I"},
    {"id":"m63", "date":"2026-06-27","time":"05:00","home":"Egypt",               "away":"Írán",               "group":"G"},
    {"id":"m64", "date":"2026-06-27","time":"05:00","home":"Nový Zéland",         "away":"Belgie",             "group":"G"},
    {"id":"m65", "date":"2026-06-27","time":"02:00","home":"Kapverdy",            "away":"Saúdská Arábie",     "group":"H"},
    {"id":"m66", "date":"2026-06-27","time":"02:00","home":"Uruguay",             "away":"Španělsko",          "group":"H"},
    {"id":"m67", "date":"2026-06-27","time":"23:00","home":"Panama",              "away":"Anglie",             "group":"L"},
    {"id":"m68", "date":"2026-06-27","time":"23:00","home":"Chorvatsko",          "away":"Ghana",              "group":"L"},
    {"id":"m69", "date":"2026-06-28","time":"04:00","home":"Alžírsko",            "away":"Rakousko",           "group":"J"},
    {"id":"m70", "date":"2026-06-28","time":"04:00","home":"Jordánsko",           "away":"Argentina",          "group":"J"},
    {"id":"m71", "date":"2026-06-28","time":"01:30","home":"Kolumbie",            "away":"Portugalsko",        "group":"K"},
    {"id":"m72", "date":"2026-06-28","time":"01:30","home":"DR Kongo",            "away":"Uzbekistán",         "group":"K"},
]

def game_kickoff_cest(game):
    naive = datetime.datetime.strptime(f"{game['date']} {game['time']}", "%Y-%m-%d %H:%M")
    return CEST.localize(naive)

def first_game_kickoff():
    return min(game_kickoff_cest(g) for g in GAMES)

def is_tippable(game):
    # Všechna tipování (zápasy i vítěz) se zamykají najednou —
    # prvním výkopem turnaje 11.6.2026 21:00 CEST.
    return datetime.datetime.now(CEST) < first_game_kickoff()

def champion_pick_open():
    return datetime.datetime.now(CEST) < first_game_kickoff()

GAMES_BY_ID = {g["id"]: g for g in GAMES}
ALL_TEAMS = sorted(set(t for g in GAMES for t in [g["home"], g["away"]]))

# ── DB ────────────────────────────────────────────────────────────────────────

def get_db():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

def init_db():
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    name       TEXT PRIMARY KEY,
                    pin_hash   TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT NOW()
                );
                CREATE TABLE IF NOT EXISTS tips (
                    user_name  TEXT NOT NULL,
                    game_id    TEXT NOT NULL,
                    home_score INTEGER NOT NULL,
                    away_score INTEGER NOT NULL,
                    updated_at TIMESTAMP DEFAULT NOW(),
                    PRIMARY KEY (user_name, game_id)
                );
                CREATE TABLE IF NOT EXISTS results (
                    game_id    TEXT PRIMARY KEY,
                    home_score INTEGER NOT NULL,
                    away_score INTEGER NOT NULL,
                    updated_at TIMESTAMP DEFAULT NOW()
                );
                CREATE TABLE IF NOT EXISTS champion_picks (
                    user_name TEXT PRIMARY KEY,
                    team      TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT NOW()
                );
            """)
        conn.commit()

try:
    init_db()
except Exception as e:
    print(f"DB init error: {e}")

def hash_pin(pin):
    return hashlib.sha256(pin.encode()).hexdigest()

def calc_points(tip, result):
    if not tip or not result: return 0
    th, ta = tip["home_score"], tip["away_score"]
    rh, ra = result["home_score"], result["away_score"]
    if th == rh and ta == ra: return 3
    def oc(h, a): return "H" if h>a else ("A" if h<a else "D")
    return 1 if oc(th,ta) == oc(rh,ra) else 0

# ── AUTH ──────────────────────────────────────────────────────────────────────

@app.route("/api/register", methods=["POST"])
def register():
    d = request.json
    name = (d.get("name") or "").strip()
    pin  = d.get("pin","")
    if not name or len(pin) < 2:
        return jsonify(error="Zadej jméno a PIN (min. 2 znaky)"), 400
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM users WHERE name=%s", (name,))
                if cur.fetchone():
                    return jsonify(error="Jméno je obsazeno"), 409
                cur.execute("INSERT INTO users (name, pin_hash) VALUES (%s,%s)", (name, hash_pin(pin)))
            conn.commit()
    except Exception as e:
        return jsonify(error=f"Chyba DB: {str(e)}"), 500
    session["user"] = name
    return jsonify(ok=True, name=name)

@app.route("/api/login", methods=["POST"])
def login():
    d = request.json
    name = (d.get("name") or "").strip()
    pin  = d.get("pin","")
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM users WHERE name=%s", (name,))
                u = cur.fetchone()
    except Exception as e:
        return jsonify(error=f"Chyba DB: {str(e)}"), 500
    if not u: return jsonify(error="Hráč nenalezen — zaregistruj se"), 404
    if u["pin_hash"] != hash_pin(pin): return jsonify(error="Špatný PIN"), 401
    session["user"] = name
    return jsonify(ok=True, name=name)

@app.route("/api/logout", methods=["POST"])
def logout():
    session.pop("user", None)
    return jsonify(ok=True)

@app.route("/api/me")
def me():
    u = session.get("user")
    if not u: return jsonify(error="Nepřihlášen"), 401
    return jsonify(name=u)

# ── ZÁPASY ────────────────────────────────────────────────────────────────────

@app.route("/api/games")
def get_games():
    now = datetime.datetime.now(CEST)
    out = []
    for g in sorted(GAMES, key=lambda x: game_kickoff_cest(x)):
        kickoff = game_kickoff_cest(g)
        mins = int((kickoff - now).total_seconds() / 60)
        out.append({
            **g,
            "display_date": kickoff.strftime("%-d.%-m."),
            "display_time": kickoff.strftime("%H:%M"),
            "tippable": now < kickoff,
            "minutes_to_kickoff": mins,
            "show_countdown": 0 < mins <= 120,
        })
    return jsonify(games=out)

# ── TIPY ──────────────────────────────────────────────────────────────────────

@app.route("/api/tips")
def get_tips():
    u = session.get("user")
    if not u: return jsonify(error="Nepřihlášen"), 401
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT game_id, home_score, away_score FROM tips WHERE user_name=%s", (u,))
            rows = cur.fetchall()
    return jsonify(tips={r["game_id"]: dict(r) for r in rows})

@app.route("/api/tips", methods=["POST"])
def save_tip():
    u = session.get("user")
    if not u: return jsonify(error="Nepřihlášen"), 401
    d = request.json
    gid, home, away = d.get("game_id"), d.get("home_score"), d.get("away_score")
    if gid is None or home is None or away is None:
        return jsonify(error="Chybí data"), 400
    game = GAMES_BY_ID.get(gid)
    if not game: return jsonify(error="Neznámý zápas"), 404
    if not is_tippable(game):
        return jsonify(error="Tipování uzavřeno — zápas již začal"), 403
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO tips (user_name, game_id, home_score, away_score, updated_at)
                VALUES (%s,%s,%s,%s,NOW())
                ON CONFLICT (user_name, game_id) DO UPDATE SET
                    home_score=EXCLUDED.home_score, away_score=EXCLUDED.away_score, updated_at=NOW()
            """, (u, gid, int(home), int(away)))
        conn.commit()
    return jsonify(ok=True)

# ── VÝSLEDKY ──────────────────────────────────────────────────────────────────

@app.route("/api/results")
def get_results():
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT game_id, home_score, away_score FROM results")
            rows = cur.fetchall()
    return jsonify(results={r["game_id"]: dict(r) for r in rows})

@app.route("/api/results", methods=["POST"])
def save_result():
    if session.get("user") != ADMIN: return jsonify(error="Pouze admin"), 403
    d = request.json
    gid, home, away = d.get("game_id"), d.get("home_score"), d.get("away_score")
    if gid is None or home is None or away is None:
        return jsonify(error="Chybí data"), 400
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO results (game_id, home_score, away_score, updated_at)
                VALUES (%s,%s,%s,NOW())
                ON CONFLICT (game_id) DO UPDATE SET
                    home_score=EXCLUDED.home_score, away_score=EXCLUDED.away_score, updated_at=NOW()
            """, (gid, int(home), int(away)))
        conn.commit()
    return jsonify(ok=True)

# ── TIP NA VÍTĚZE ─────────────────────────────────────────────────────────────

@app.route("/api/champion")
def get_champion():
    u = session.get("user")
    if not u: return jsonify(error="Nepřihlášen"), 401
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT team FROM champion_picks WHERE user_name=%s", (u,))
            row = cur.fetchone()
    return jsonify(pick=row["team"] if row else None, open=champion_pick_open(), teams=ALL_TEAMS)

@app.route("/api/champion", methods=["POST"])
def save_champion():
    u = session.get("user")
    if not u: return jsonify(error="Nepřihlášen"), 401
    if not champion_pick_open():
        return jsonify(error="Tipování vítěze je uzavřeno — turnaj již začal"), 403
    team = (request.json or {}).get("team","").strip()
    if team not in ALL_TEAMS: return jsonify(error="Neplatný tým"), 400
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO champion_picks (user_name, team, updated_at) VALUES (%s,%s,NOW())
                ON CONFLICT (user_name) DO UPDATE SET team=EXCLUDED.team, updated_at=NOW()
            """, (u, team))
        conn.commit()
    return jsonify(ok=True)

@app.route("/api/champion/result", methods=["GET","POST"])
def champion_result():
    if request.method == "POST":
        if session.get("user") != ADMIN: return jsonify(error="Pouze admin"), 403
        team = (request.json or {}).get("team","").strip()
        if team not in ALL_TEAMS: return jsonify(error="Neplatný tým"), 400
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO champion_picks (user_name, team, updated_at) VALUES ('__result__',%s,NOW())
                    ON CONFLICT (user_name) DO UPDATE SET team=EXCLUDED.team, updated_at=NOW()
                """, (team,))
            conn.commit()
        return jsonify(ok=True)
    else:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT team FROM champion_picks WHERE user_name='__result__'")
                row = cur.fetchone()
        return jsonify(result=row["team"] if row else None)

# ── ŽEBŘÍČEK ──────────────────────────────────────────────────────────────────

@app.route("/api/leaderboard")
def leaderboard():
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT name FROM users WHERE name!=%s", (ADMIN,))
            users = [r["name"] for r in cur.fetchall()]
            cur.execute("SELECT game_id, home_score, away_score FROM results")
            results = {r["game_id"]: dict(r) for r in cur.fetchall()}
            cur.execute("SELECT user_name, team FROM champion_picks WHERE user_name NOT IN ('__result__', %s)", (ADMIN,))
            champ_picks = {r["user_name"]: r["team"] for r in cur.fetchall()}
            cur.execute("SELECT team FROM champion_picks WHERE user_name='__result__'")
            cr = cur.fetchone()
            champ_result = cr["team"] if cr else None
    rows = []
    with get_db() as conn:
        with conn.cursor() as cur:
            for name in users:
                cur.execute("SELECT game_id, home_score, away_score FROM tips WHERE user_name=%s", (name,))
                user_tips = {r["game_id"]: dict(r) for r in cur.fetchall()}
                total = exact = correct = 0
                for gid, res in results.items():
                    p = calc_points(user_tips.get(gid), res)
                    total += p
                    if p==3: exact+=1
                    if p==1: correct+=1
                rows.append({"name":name,"total":total,"exact":exact,"correct":correct,
                             "champ_pick":champ_picks.get(name)})
    rows.sort(key=lambda x: x["total"], reverse=True)
    return jsonify(leaderboard=rows, champion_result=champ_result)

# ── ADMIN ─────────────────────────────────────────────────────────────────────

@app.route("/api/admin/users")
def admin_users():
    if session.get("user") != ADMIN: return jsonify(error="Pouze admin"), 403
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT name, created_at FROM users WHERE name!=%s ORDER BY created_at", (ADMIN,))
            users = [dict(r) for r in cur.fetchall()]
    return jsonify(users=users)

@app.route("/api/admin/users/<name>", methods=["DELETE"])
def admin_delete_user(name):
    if session.get("user") != ADMIN: return jsonify(error="Pouze admin"), 403
    if name == ADMIN: return jsonify(error="Nemůžeš smazat Admin účet"), 400
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM tips WHERE user_name=%s", (name,))
            cur.execute("DELETE FROM champion_picks WHERE user_name=%s", (name,))
            cur.execute("DELETE FROM users WHERE name=%s", (name,))
        conn.commit()
    return jsonify(ok=True)

@app.route("/api/admin/all-tips")
def admin_all_tips():
    if session.get("user") != ADMIN: return jsonify(error="Pouze admin"), 403
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT name FROM users WHERE name!=%s ORDER BY name", (ADMIN,))
            users = [r["name"] for r in cur.fetchall()]
            cur.execute("SELECT user_name, game_id, home_score, away_score FROM tips")
            tips_rows = cur.fetchall()
            cur.execute("SELECT user_name, team FROM champion_picks WHERE user_name!='__result__'")
            champ_rows = cur.fetchall()
    tips_by_user = {}
    for r in tips_rows:
        tips_by_user.setdefault(r["user_name"],{})[r["game_id"]] = {"home":r["home_score"],"away":r["away_score"]}
    return jsonify(users=users, tips=tips_by_user, champion_picks={r["user_name"]:r["team"] for r in champ_rows})

# ── STATIC ────────────────────────────────────────────────────────────────────

@app.route("/", defaults={"path":""})
@app.route("/<path:path>")
def index(path):
    return send_from_directory("static", "index.html")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
