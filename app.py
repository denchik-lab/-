import random, os, json
from flask import Flask, render_template, request, redirect, url_for
from heroes_db import ALL_DOTA_HEROES
from items_db import ALL_DOTA_ITEMS

app = Flask(__name__)
SAVE_FILE = os.path.join(app.root_path, 'progress.json')

def load_progress():
    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("score", {"correct": 0, "total": 0, "mmr": 1000}), data.get("high_score", 0)
        except Exception:
            pass
    return {"correct": 0, "total": 0, "mmr": 1000}, 0

def save_progress():
    with open(SAVE_FILE, 'w', encoding='utf-8') as f:
        json.dump({"score": score, "high_score": high_score}, f, ensure_ascii=False, indent=4)

score, high_score = load_progress()

def get_hero_img_path(hero_obj):
    local_path = os.path.join(app.root_path, 'static', 'heroes')
    clean = hero_obj["url_name"].lower().strip()
    if os.path.exists(local_path):
        for f in os.listdir(local_path):
            if f.lower().startswith(clean): return f"/static/heroes/{f}"
    return ""

def get_item_img_path(item_obj):
    local_path = os.path.join(app.root_path, 'static', 'items')
    clean = item_obj["url_name"].lower().replace("_", "").replace("-", "").replace(" ", "").strip()
    if os.path.exists(local_path):
        for f in os.listdir(local_path):
            f_clean = os.path.splitext(f)[0].lower().replace("_", "").replace("-", "").replace(" ", "")
            if f_clean == clean or clean in f_clean: return f"/static/items/{f}"
    return ""

def get_rank_info(mmr):
    if mmr < 1500: return "Рекрут"
    elif mmr < 2500: return "Герой"
    elif mmr < 3500: return "Властелин"
    elif mmr < 4500: return "Божество"
    return "Божественный Титан"

def get_rank_progress(mmr):
    if mmr < 1500: return int((mmr / 1500) * 100), 1500, "Герой"
    elif mmr < 2500: return int(((mmr - 1500) / 1000) * 100), 2500, "Властелин"
    elif mmr < 3500: return int(((mmr - 2500) / 1000) * 100), 3500, "Божество"
    elif mmr < 4500: return int(((mmr - 3500) / 1000) * 100), 4500, "Божественный Титан"
    return 100, mmr, "Макс. ранг"

def get_hero_counters_and_reasons(hero_name, hero_type, hero_tag):
    if hero_type == "str":
        counters = ["Timbersaw", "Lifestealer", "Ursa"]
        reasons = {"Timbersaw": "наносит чистый урон пилами.", "Lifestealer": "пожирает ХП пассивкой Feast.", "Ursa": "разрывает стаками Fury Swipes."}
    elif hero_type == "agi":
        counters = ["Axe", "Slardar", "Razor"]
        reasons = {"Axe": "агрит Блинком сквозь БКБ.", "Slardar": "срезает в ноль всю броню.", "Razor": "лишает урона через Static Link."}
    else:
        counters = ["Anti-Mage", "Silencer", "Nyx Assassin"]
        reasons = {"Anti-Mage": "выжигает весь запас маны.", "Silencer": "накладывает Глобал Сайленс.", "Nyx Assassin": "выжигает ману по интеллекту."}
    if hero_tag == "invisible":
        counters = ["Slardar", "Zeus", "Bounty Hunter"]; reasons = {"Slardar": "раскрывает инвиз.", "Zeus": "находит молниями.", "Bounty Hunter": "вешает Трек."}
    elif hero_tag == "illusion":
        counters = ["Sven", "Earthshaker", "Axe"]; reasons = {"Sven": "уничтожает сплешем.", "Earthshaker": "взрывает Echo Slam.", "Axe": "крутится от толпы."}
    elif hero_tag == "heal":
        counters = ["Ancient Apparition", "Necrophos", "Doom"]; reasons = {"Ancient Apparition": "отключает реген.", "Necrophos": "добивает Косой.", "Doom": "выключает пассивное лечение."}
    return counters, reasons

@app.route('/')
def index():
    global high_score
    current_mode = request.args.get('mode', 'heroes')
    current_filter = request.args.get('filter', 'all')
    current_diff = request.args.get('diff', 'normal')

    # Настройка времени от сложности
    if current_diff == 'easy': max_time = 30
    elif current_diff == 'hard': max_time = 7
    else: max_time = 30 if current_mode == 'items' else 15

    active_rune, rune_title = "none", ""
    if random.random() < 0.25:
        active_rune = random.choice(["dd", "haste", "regen"])
        if active_rune == "dd": rune_title = "⚔️ Руна Двойного Урона (x2 PTS)"
        elif active_rune == "haste": rune_title, max_time = "⚡ Руна Ускорения (5 секунд! +15 PTS бонус)", 5
        elif active_rune == "regen": rune_title = "💚 Руна Регенерации (Защита очков)"

    rank_name = get_rank_info(score["mmr"])
    rank_percent, next_mmr, next_rank = get_rank_progress(score["mmr"])

    if current_mode == "items":
        enemy_item = random.choice(ALL_DOTA_ITEMS)
        enemy_name = enemy_item["display_name"]
        options_texts = enemy_item["wrong_descs"] + [enemy_item["correct_desc"]]
        random.shuffle(options_texts)
        options = [{"key": txt, "name": txt, "img_src": None} for txt in options_texts]
        return render_template('index.html', enemy_key=enemy_name, enemy_type=enemy_item["type"], enemy_tag="item", enemy=enemy_name, enemy_url=get_item_img_path(enemy_item), options=options, score=score, high_score=high_score, current_filter=current_filter, current_diff=current_diff, rank_name=rank_name, rank_percent=rank_percent, next_mmr=next_mmr, next_rank=next_rank, active_rune=active_rune, rune_title=rune_title, max_time=max_time, current_mode=current_mode)
    else:
        filtered_heroes = [h for h in ALL_DOTA_HEROES if h.get("type") == current_filter] if current_filter in ['str', 'agi', 'int'] else ALL_DOTA_HEROES
        enemy_hero = random.choice(filtered_heroes)
        enemy_name = enemy_hero["display_name"]
        correct_counters, _ = get_hero_counters_and_reasons(enemy_name, enemy_hero.get("type", "str"), enemy_hero.get("tag", "fat"))
        correct_display = random.choice(correct_counters)
        correct_obj = next((f for f in ALL_DOTA_HEROES if f["display_name"] == correct_display), {"display_name": correct_display, "url_name": correct_display.lower().replace(" ", "_")})
        wrong_pool = [h for h in ALL_DOTA_HEROES if h["display_name"] != enemy_name and h["display_name"] not in correct_counters]
        wrong_answers = random.sample(wrong_pool, 3)
        options_objs = wrong_answers + [correct_obj]
        random.shuffle(options_objs)
        options = [{"key": h["display_name"], "name": h["display_name"], "img_src": get_hero_img_path(h)} for h in options_objs]
        return render_template('index.html', enemy_key=enemy_name, enemy_type=enemy_hero.get("type", "str"), enemy_tag=enemy_hero.get("tag", "fat"), enemy=enemy_name, enemy_url=get_hero_img_path(enemy_hero), options=options, score=score, high_score=high_score, current_filter=current_filter, current_diff=current_diff, rank_name=rank_name, rank_percent=rank_percent, next_mmr=next_mmr, next_rank=next_rank, active_rune=active_rune, rune_title=rune_title, max_time=max_time, current_mode=current_mode)

@app.route('/wiki')
def wiki():
    heroes_list = [{"name": h["display_name"], "type": h.get("type", "str"), "tag": h.get("tag", "fat"), "img_src": get_hero_img_path(h), "counters": get_hero_counters_and_reasons(h["display_name"], h.get("type", "str"), h.get("tag", "fat")), "reasons": get_hero_counters_and_reasons(h["display_name"], h.get("type", "str"), h.get("tag", "fat"))} for h in ALL_DOTA_HEROES]
    items_list = [{"name": i["display_name"], "type": i.get("type", "item"), "img_src": get_item_img_path(i), "desc": i.get("correct_desc", "")} for i in ALL_DOTA_ITEMS]
    return render_template('wiki.html', heroes=heroes_list, items=items_list, score=score, high_score=high_score, rank_name=get_rank_info(score["mmr"]))

@app.route('/check', methods=['POST'])
def check():
    global high_score
    enemy_name = request.form.get('enemy')
    selected_name = request.form.get('choice')
    enemy_type = request.form.get('enemy_type', 'str')
    enemy_tag = request.form.get('enemy_tag', 'fat')
    current_filter = request.form.get('current_filter', 'all')
    active_rune = request.form.get('active_rune', 'none')
    current_mode = request.form.get('current_mode', 'heroes')
    current_diff = request.form.get('current_diff', 'normal')

    if not enemy_name: return redirect(url_for('index', mode=current_mode, diff=current_diff))

    score["total"] += 1
    # Базовые очки от сложности
    base_win = 15 if current_diff == 'easy' else (40 if current_diff == 'hard' else 25)
    base_lose = 10 if current_diff == 'easy' else (35 if current_diff == 'hard' else 25)

    win_pts = base_win * 2 if active_rune == "dd" else (base_win + 15 if active_rune == "haste" else base_win)
    lose_pts = 0 if active_rune == "regen" else base_lose

    if current_mode == "items":
        item_obj = next((i for i in ALL_DOTA_ITEMS if i["display_name"] == enemy_name), None)
        is_correct = (selected_name == item_obj["correct_desc"]) if item_obj else False
        res_win = f"Правильно! Это верная игровая механика для {enemy_name}."
        res_lose = f"Неверно! Настоящее описание предмета {enemy_name}: <br><br> • {item_obj['correct_desc'] if item_obj else ''}"
        tips = None
    else:
        correct_counters, reasons_dict = get_hero_counters_and_reasons(enemy_name, enemy_type, enemy_tag)
        is_correct = selected_name in correct_counters
        res_win = f"Правильно! {selected_name} контрит {enemy_name}, потому что {reasons_dict.get(selected_name, '')}"
        res_lose = f"Неверно! Хороший выбор против {enemy_name}:"
        tips = [f"• {h} — потому что {t}" for h, t in reasons_dict.items()]

    if is_correct and selected_name != "timeout":
        score["correct"] += 1
        score["mmr"] += win_pts
        if score["correct"] > high_score: high_score = score["correct"]
        save_progress()
        rank_name = get_rank_info(score["mmr"])
        rank_percent, next_mmr, next_rank = get_rank_progress(score["mmr"])
        return render_template('result.html', result=res_win, tips=None, color="#2ecc71", score=score,
                               high_score=high_score, sound_type="win", current_filter=current_filter,
                               current_diff=current_diff, rank_name=rank_name, rank_percent=rank_percent,
                               next_mmr=next_mmr, next_rank=next_rank, mmr_change=f"+{win_pts} PTS 📈",
                               current_mode=current_mode)
    else:
        score["mmr"] = max(0, score["mmr"] - lose_pts)
        save_progress()
        final_res = f"⏱️ Время вышло! Вы потеряли очки. Правильный выбор: {enemy_name}" if selected_name == "timeout" else res_lose
        mmr_change, color = ("0 PTS 💚", "#e67e22") if active_rune == "regen" else (f"-{lose_pts} PTS 🩸", "#e74c3c")
        rank_name = get_rank_info(score["mmr"])
        rank_percent, next_mmr, next_rank = get_rank_progress(score["mmr"])
        return render_template('result.html', result=final_res, tips=tips, color=color, score=score,
                               high_score=high_score, sound_type="lose", current_filter=current_filter,
                               current_diff=current_diff, rank_name=rank_name, rank_percent=rank_percent,
                               next_mmr=next_mmr, next_rank=next_rank, mmr_change=mmr_change, current_mode=current_mode)

@app.route('/reset')
def reset():
    score["correct"], score["total"], score["mmr"] = 0, 0, 1000
    save_progress()
    return redirect(url_for('index'))
if __name__ == '__main__':
    app.run(debug=True, port=5001)
