"""Кошти 1.2 — локальний фінансовий трекер з архівом та інтерактивними графіками.
Python 3.10+, без залежностей. Запуск: python finance_tracker.py
Відкрити: http://127.0.0.1:8000
Для перенесення історії скопіюйте finance.sqlite3 поруч із цим файлом.
"""
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, urlencode
from pathlib import Path
from decimal import Decimal, InvalidOperation
from datetime import date
import calendar, sqlite3, os, secrets, html, argparse

STYLE = '*{box-sizing:border-box} :root{--bg:#fff;--surface:#f9f8f7;--text:#2c2c2b;--muted:#686660;--border:#e6e5e3;--blue:#246fbb;--green:#28754d;--red:#b6372c;--purple:#9b6bb6}body{margin:0;background:var(--surface);color:var(--text);font:16px/1.5 system-ui,-apple-system,sans-serif}main{max-width:1120px;margin:auto;padding:40px 24px}header{display:flex;justify-content:space-between;align-items:center;gap:24px;margin-bottom:32px}.brand{font-weight:750;letter-spacing:2px;color:var(--blue)}.brand span{font-size:12px;color:var(--muted);letter-spacing:1px;margin-left:12px}h1{font-size:32px;letter-spacing:-1px;line-height:1.2;margin:16px 0 12px}h2{font-size:20px;margin:0 0 20px}p{margin:0}.muted,small{color:var(--muted);font-size:14px}.filter{display:flex;align-items:center;gap:8px;flex-wrap:wrap}.filter label{width:100%;font-size:14px;color:var(--muted)}input,select,button{font:inherit;border:1px solid var(--border);border-radius:8px;background:var(--bg);color:var(--text);min-height:44px;padding:10px 12px}input,select{width:100%;min-width:0}button{cursor:pointer;font-weight:600}.filter input{width:172px}.primary{background:var(--blue);color:white;border-color:var(--blue);width:100%;margin-top:8px}a{color:var(--blue)}:focus-visible{outline:3px solid var(--blue);outline-offset:3px}.metrics{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-bottom:24px}.metrics article,.panel{border:1px solid var(--border);background:var(--bg);border-radius:12px;padding:24px}.metrics p{font-size:14px;color:var(--muted);margin-bottom:8px}.metrics strong{font-size:28px;letter-spacing:-.6px;font-variant-numeric:tabular-nums}.metrics small{display:block;margin-top:8px}.positive{color:var(--green)}.negative{color:var(--red)}.layout{display:grid;grid-template-columns:320px minmax(0,1fr);gap:24px;align-items:start}.entry{display:grid;gap:16px}.entry label{display:grid;gap:6px;font-size:14px}.chart-stack{display:grid;gap:24px}.bar-row{margin-bottom:16px}.bar-row:last-child{margin-bottom:0}.bar-label{display:flex;justify-content:space-between;gap:16px;font-size:14px;margin-bottom:8px}.bar-label strong{font-variant-numeric:tabular-nums}.track{height:8px;background:var(--surface);border-radius:4px}.bar{height:8px;background:#5e9fe8;border-radius:4px}svg{display:block;width:100%;height:auto;margin-top:12px}svg text{font:14px system-ui;fill:var(--muted)}.grid{stroke:var(--border)}.line{stroke:var(--purple);stroke-width:2;fill:none}.area{fill:var(--purple);opacity:.12}circle{fill:var(--purple)}.history{margin-top:24px}.section-heading{display:flex;justify-content:space-between;align-items:baseline;gap:16px}.table-scroll{overflow-x:auto}table{min-width:650px;border-collapse:collapse;width:100%;font-size:14px}th{font-weight:500;color:var(--muted);text-align:left;white-space:nowrap}td,th{padding:12px 8px;border-bottom:1px solid var(--border)}td{overflow-wrap:anywhere}.num{text-align:right;white-space:nowrap;font-variant-numeric:tabular-nums}.badge{display:inline-block;padding:4px 8px;border-radius:4px;background:var(--surface);white-space:nowrap}.income{color:var(--green)}.expense{color:var(--red)}.actions{display:flex;align-items:center;gap:8px}.actions a{display:inline-flex;align-items:center;min-height:44px}.actions form{margin:0}.delete{font-size:24px;color:var(--red);width:44px;padding:0}.empty{padding:24px 0;color:var(--muted);font-size:14px}.error{padding:12px;border:1px solid var(--red);border-radius:8px;color:var(--red);margin-bottom:16px}details table{min-width:0}details{margin-top:12px;font-size:14px}summary{cursor:pointer;min-height:44px;padding-top:12px}footer{font-size:14px;color:var(--muted);padding:24px 0 0}@media(max-width:760px){main{padding:24px 16px}header{display:block}.filter{margin-top:24px}.metrics{grid-template-columns:1fr}.layout{grid-template-columns:1fr}.metrics strong{font-size:26px}.panel{padding:20px}.brand span{display:block;margin:4px 0 0}.section-heading{display:block;margin-bottom:16px}.section-heading h2{margin-bottom:8px}h1{font-size:28px}}@media(prefers-color-scheme:dark){:root{--bg:#202020;--surface:#191919;--text:#fff;--muted:#b6b4b0;--border:#494947;--blue:#5e9fe8;--green:#72bc8f;--red:#e97366;--purple:#bf8eda}.primary{color:#191919}}\n@media(max-width:760px){svg text{font-size:24px}.history td:first-child{white-space:nowrap} .history td{overflow-wrap:normal}}\n\n.tabs{display:flex;gap:8px;margin-bottom:32px;border-bottom:1px solid var(--border);padding-bottom:8px}.tabs a{display:inline-flex;align-items:center;min-height:44px;padding:8px 16px;text-decoration:none;border-radius:8px;color:var(--muted)}.tabs a[aria-current=page]{background:var(--bg);color:var(--blue);font-weight:650;border:1px solid var(--border)}.archive-filters{margin-bottom:24px}.archive-form{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:16px}.archive-form label{display:grid;gap:6px;font-size:14px}.search-field{grid-column:span 2}.filter-actions{grid-column:span 2;display:flex;align-items:end;gap:16px}.filter-actions .primary{width:auto;margin:0;flex:1}.filter-actions a{display:inline-flex;align-items:center;min-height:44px}.archive-caption{margin:0 0 16px}.month-link{display:inline-flex;align-items:center;min-height:44px;white-space:nowrap}.pagination{display:flex;align-items:center;justify-content:space-between;gap:16px;flex-wrap:wrap;margin-top:20px}.pagination div{display:flex;gap:16px}.pagination a{display:inline-flex;align-items:center;min-height:44px}@media(max-width:760px){.archive-form{grid-template-columns:1fr 1fr}.search-field,.filter-actions{grid-column:span 2}.archive-header{margin-bottom:24px}.archive-caption{line-height:1.6}}\n\n.category-caption{margin:-8px 0 20px}.category-share{margin-top:6px;font-variant-numeric:tabular-nums}.chart-switch{display:flex;gap:4px;flex-wrap:wrap;margin-bottom:16px}.chart-switch a{min-height:44px;display:inline-flex;align-items:center;padding:8px 12px;border:1px solid var(--border);border-radius:8px;font-size:14px;text-decoration:none;color:var(--muted)}.chart-switch a[aria-current=true]{color:var(--blue);border-color:var(--blue);background:var(--surface);font-weight:650}.chart-hint{margin-bottom:12px}.chart-empty{margin-bottom:12px}.week-bar{fill:#5e9fe8}.hit-region{fill:transparent;stroke:none}.chart-hit:hover .hit-region,.chart-hit:focus .hit-region{fill:var(--blue);fill-opacity:.12}.hit-region.selected{fill:var(--blue);fill-opacity:.08;stroke:var(--blue);stroke-width:1}.chart-hit:focus-visible{outline:none}.history-filter{display:flex;justify-content:space-between;gap:16px;align-items:center;flex-wrap:wrap;margin-bottom:16px;padding:12px 16px;background:var(--surface);border-radius:8px;font-size:14px}.reset-day{display:inline-flex;align-items:center;min-height:44px}.day-picker{display:flex;gap:8px;flex-wrap:wrap;margin-top:16px;align-items:center}.day-picker label{font-size:14px;color:var(--muted);width:100%}.day-picker input{width:180px}.series-table,.category-table{min-width:0}.series-table a{display:inline-flex;align-items:center;min-height:44px}.time-chart svg{width:100%;margin-top:0}.time-chart svg text{font-size:20px}.time-chart svg circle{pointer-events:none}#history{scroll-margin-top:16px}@media(max-width:760px){.time-chart svg text{font-size:24px}.chart-switch a{flex:1;justify-content:center;padding:8px}.chart-switch{gap:8px}.day-picker input{flex:1;min-width:140px;width:auto}.day-picker button{flex:1}.category-table th,.category-table td{padding:12px 4px;font-size:14px}}\n'

ROOT = Path(__file__).resolve().parent
DB = Path(os.environ.get('FINANCE_DB', str(ROOT / 'finance.sqlite3')))
TOKEN = secrets.token_urlsafe(32)
CATEGORIES = ('Продукти', 'Транспорт', 'Житло', 'Здоров’я', 'Розваги', 'Покупки', 'Освіта', 'Зарплата', 'Інше')
def esc(value): return html.escape(str(value), quote=True)
def money(cents): return f'{cents / 100:,.2f}'.replace(',', ' ').replace('.', ',') + ' ₴'
class DatabaseConnection(sqlite3.Connection):
    def __exit__(self, exc_type, exc_value, traceback):
        try: return super().__exit__(exc_type, exc_value, traceback)
        finally: self.close()

def connect():
    con = sqlite3.connect(DB, timeout=10, factory=DatabaseConnection)
    con.row_factory = sqlite3.Row
    con.create_function("casefold", 1, lambda value: str(value).casefold(), deterministic=True)
    return con

def init_db():
    DB.parent.mkdir(parents=True, exist_ok=True)
    with connect() as con:
        con.execute("""CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY, day TEXT NOT NULL, kind TEXT NOT NULL CHECK(kind IN ('income','expense')),
        category TEXT NOT NULL, amount INTEGER NOT NULL CHECK(amount > 0), note TEXT NOT NULL DEFAULT '')""")
        con.execute('CREATE INDEX IF NOT EXISTS idx_day ON transactions(day)')

def validate(form):
    day = date.fromisoformat(form.get('day', '')).isoformat()
    kind, category = form.get('kind'), form.get('category')
    if kind not in ('income', 'expense') or category not in CATEGORIES: raise ValueError('Неправильний тип або категорія.')
    try:
        val = Decimal(form.get('amount', '').replace(',', '.'))
        if not val.is_finite() or val <= 0 or val > Decimal('100000000') or val != val.quantize(Decimal('.01')):
            raise ValueError('Сума має бути від 0,01 до 100 000 000 грн, до двох знаків після коми.')
    except InvalidOperation: raise ValueError('Введіть коректну суму.')
    note = form.get('note', '').strip()
    if len(note) > 200: raise ValueError('Опис: максимум 200 символів.')
    return day, kind, category, int(val * 100), note

def month_rows(month):
    start = date.fromisoformat(month + '-01')
    end = date(start.year + (start.month == 12), start.month % 12 + 1, 1)
    with connect() as con:
        return con.execute('SELECT * FROM transactions WHERE day >= ? AND day < ? ORDER BY day DESC, id DESC', (start.isoformat(), end.isoformat())).fetchall()

def stats(rows):
    inc = sum(r['amount'] for r in rows if r['kind'] == 'income')
    exp = sum(r['amount'] for r in rows if r['kind'] == 'expense')
    cats, days = {}, {}
    for r in rows:
        if r['kind'] == 'expense':
            cats[r['category']] = cats.get(r['category'], 0) + r['amount']
            days[r['day']] = days.get(r['day'], 0) + r['amount']
    return inc, exp, cats, days

CHART_VIEWS = {'days': 'За днями', 'weeks': 'За тижнями', 'cumulative': 'Накопичено'}

def home_link(month, view='days', day='', week='', edit=None, anchor=''):
    params = {'month': month, 'view': view}
    if day: params['day'] = day
    if week: params['week'] = week
    if edit: params['edit'] = edit
    return '/?' + urlencode(params) + (('#' + anchor) if anchor else '')

def month_dates(month):
    first = date.fromisoformat(month + '-01')
    if first.strftime('%Y-%m') != month or len(month) != 7:
        raise ValueError('Некоректний місяць.')
    return [date(first.year, first.month, i).isoformat() for i in range(1, calendar.monthrange(first.year, first.month)[1]+1)]

def chart_series(days, month, view='days'):
    if view not in CHART_VIEWS: raise ValueError('Некоректний режим графіка.')
    dates = month_dates(month)
    records = [{'start':d, 'end':d, 'label':d[-2:], 'amount':days.get(d,0)} for d in dates]
    if view == 'cumulative':
        total = 0
        for r in records:
            total += r['amount']; r['amount'] = total
    if view == 'weeks':
        groups = []
        for r in records:
            if not groups or date.fromisoformat(r['start']).weekday() == 0:
                groups.append(dict(r))
            else:
                groups[-1]['end'] = r['end']; groups[-1]['amount'] += r['amount']
        for r in groups: r['label'] = r['start'][-2:] + '–' + r['end'][-2:]
        return groups
    return records

def history_selection(month, day='', week=''):
    dates = month_dates(month)
    if day and week: raise ValueError('Оберіть лише день або тиждень.')
    if day:
        if day not in dates: raise ValueError('День має належати обраному місяцю.')
        return day, day
    if week:
        match = next((r for r in chart_series({},month,'weeks') if r['start'] == week), None)
        if not match: raise ValueError('Некоректний тиждень.')
        return match['start'], match['end']
    return '', ''

def top_categories(cats):
    ordered = sorted(cats.items(), key=lambda item: (-item[1], item[0]))
    result = [{'label':k, 'amount':v, 'rest':False} for k,v in ordered[:5]]
    if len(ordered)>5:
        result.append({'label':'Решта категорій', 'amount':sum(v for _,v in ordered[5:]), 'rest':True})
    return result

def charts(cats, days, month, view='days', day='', week=''):
    records = chart_series(days,month,view)
    total = sum(cats.values())
    if total:
        peak = max(r['amount'] for r in top_categories(cats))
        bars = ''
        for r in top_categories(cats):
            color = 'var(--muted)' if r['rest'] else '#5e9fe8'
            share = r['amount'] / total * 100
            bars += f'<div class="bar-row"><div class="bar-label"><span>{esc(r["label"])}</span><strong>{money(r["amount"])}</strong></div><div class="track"><div class="bar" style="background:{color};width:{r["amount"]/peak*100:.2f}%"></div></div><p class="category-share muted">{share:.1f}% витрат місяця</p></div>'
        full = ''.join(f'<tr><td>{esc(k)}</td><td class="num">{money(v)}</td><td class="num">{v/total*100:.1f}%</td></tr>' for k,v in sorted(cats.items(),key=lambda item:(-item[1],item[0])))
        bars += f'<details><summary>Усі категорії та точні суми</summary><div class="table-scroll"><table class="category-table"><thead><tr><th>Категорія</th><th class="num">Сума</th><th class="num">Частка</th></tr></thead><tbody>{full}</tbody></table></div></details>'
    else: bars = '<p class="empty">Витрат поки немає. Додайте першу операцію.</p>'
    switches = ''.join(f'<a href="{esc(home_link(month,key,day,week))}" {"aria-current=true" if key==view else ""}>{label}</a>' for key,label in CHART_VIEWS.items())
    controls = f'<nav class="chart-switch" aria-label="Режим графіка">{switches}</nav>'
    subtitle = {'days':'Щоденні витрати · клік по дню фільтрує історію', 'weeks':'Тижні пн–нд у межах місяця · клік фільтрує історію', 'cumulative':'Сума витрат від початку місяця · клік показує лише вибраний день'}[view]
    count = len(records); width = 600; left = 110; right = 576; baseline = 194
    highest = max(r['amount'] for r in records)
    # Five zero-based currency ticks with a human-scale 1/2/5 step, in integer cents.
    raw = max(100,(highest+3)//4); magnitude = 10 ** (len(str(raw))-1)
    step = next(n*magnitude for n in (1,2,5,10) if n*magnitude>=raw)
    ceiling = step*4
    y = lambda val: baseline - val/ceiling*156
    weekly = view == 'weeks'
    pitch = (right-left)/count if weekly else (right-left)/(count-1)
    x = lambda i: left + (i+.5)*pitch if weekly else left+i*pitch
    def axis_label(cents):
        if cents >= 100000000: return f'{cents/100000000:g} млн'
        if cents >= 100000: return f'{cents/100000:g} тис.'
        return f'{cents/100:g}'
    grid = ''.join(f'<line x1="{left}" x2="{right}" y1="{y(step*j):.2f}" y2="{y(step*j):.2f}" class="grid"/><text x="102" y="{y(step*j)+4:.2f}" text-anchor="end">{axis_label(step*j)}</text>' for j in range(5))
    # Desktop labels also use a compact alternate string on narrow screens.
    if weekly:
        ticks = ''.join(f'<text x="{x(i):.2f}" y="223" text-anchor="middle">{r["label"]}</text>' for i,r in enumerate(records))
    else:
        indices = sorted(set([0,7,14,21,count-1]))
        ticks = ''.join(f'<text x="{x(i):.2f}" y="223" text-anchor="middle">{records[i]["label"]}</text>' for i in indices)
    geometry = ''
    if weekly:
        for i,r in enumerate(records):
            w = min(52,pitch*.65)
            geometry += f'<rect x="{x(i)-w/2:.2f}" y="{y(r["amount"]):.2f}" width="{w:.2f}" height="{baseline-y(r["amount"]):.2f}" class="week-bar"/>'
    else:
        points = ' '.join(f'{x(i):.2f},{y(r["amount"]):.2f}' for i,r in enumerate(records))
        geometry = f'<polygon points="{left},{baseline} {points} {right},{baseline}" class="area"/><polyline points="{points}" class="line"/>'
        geometry += ''.join(f'<circle cx="{x(i):.2f}" cy="{y(r["amount"]):.2f}" r="3"/>' for i,r in enumerate(records))
    hits = ''; detail_rows = ''
    for i,r in enumerate(records):
        target = home_link(month,view,week=r['start'],anchor='history') if weekly else home_link(month,view,day=r['start'],anchor='history')
        label = r['start'] + (' — '+r['end'] if weekly else '')
        accessible = f'{label}: {money(r["amount"])}. Показати операції.'
        hit_left = max(left-8, x(i)-pitch/2); hit_right = min(right+8,x(i)+pitch/2)
        selected = week==r['start'] if weekly else day==r['start']
        hits += f'<a href="{esc(target)}" aria-label="{esc(accessible)}" class="chart-hit"><title>{esc(accessible)}</title><rect x="{hit_left:.2f}" y="30" width="{hit_right-hit_left:.2f}" height="170" class="hit-region {"selected" if selected else ""}"/></a>'
        detail_rows += f'<tr><td><a href="{esc(target)}">{esc(label)}</a></td><td class="num">{money(r["amount"])}</td></tr>'
    day_form = f'<form method="get" class="day-picker"><input type="hidden" name="month" value="{month}"><input type="hidden" name="view" value="{view}"><label for="pick-day">Операції конкретного дня</label><input id="pick-day" name="day" type="date" min="{month_dates(month)[0]}" max="{month_dates(month)[-1]}" value="{day}" required><button>Показати день</button></form>'
    value_title = 'Накопичені витрати' if view=='cumulative' else 'Витрати'
    chart = controls + f'<p class="muted chart-hint">{subtitle}. Вісь Y — грн.</p>'
    if not total: chart += '<p class="muted chart-empty">За місяць записаних витрат немає. Дні з доходами також можна обрати.</p>'
    chart += f'<div class="time-chart"><svg viewBox="0 0 600 244" aria-label="{esc(CHART_VIEWS[view])}: витрати за {month}. Використайте посилання на дні або таблицю значень." role="group">{grid}{geometry}{hits}{ticks}</svg></div>'
    chart += day_form + f'<details><summary>Точні суми та вибір періоду</summary><div class="table-scroll"><table class="series-table"><thead><tr><th>Дата / період</th><th class="num">{value_title}</th></tr></thead><tbody>{detail_rows}</tbody></table></div></details>'
    return bars, chart


def render(month, edit_id=None, error='', form=None, view='days', day='', week=''):
    if view not in CHART_VIEWS: raise ValueError('Некоректний режим графіка.')
    first, last = history_selection(month, day, week)
    month_all = month_rows(month); inc, exp, cats, days = stats(month_all)
    rows = [r for r in month_all if first <= r['day'] <= last] if first else month_all
    selection_label = day or (f'{first} — {last}' if week else 'Увесь місяць')
    reset_link = home_link(month, view, anchor='history')
    clear_filter = f'<a class="reset-day" href="{esc(reset_link)}">Показати весь місяць</a>' if first else ''
    selection_banner = f'<div class="history-filter"><span>Таблиця: <strong>{esc(selection_label)}</strong></span>{clear_filter}</div>'
    context_fields = f'<input type="hidden" name="view" value="{view}"><input type="hidden" name="filter_day" value="{day}"><input type="hidden" name="filter_week" value="{week}">'
    editing = None
    if edit_id:
        with connect() as con: editing = con.execute('SELECT * FROM transactions WHERE id=?',(edit_id,)).fetchone()
    f = dict(editing) if editing else {'day':date.today().isoformat(), 'kind':'expense','category':'Продукти','note':'','amount':''}
    if editing: f['amount'] = f"{editing['amount']/100:.2f}"
    if form: f.update(form)
    options = ''.join(f'<option {"selected" if c==f["category"] else ""}>{esc(c)}</option>' for c in CATEGORIES)
    bars, line = charts(cats, days, month, view, day, week)
    trs = ''
    for r in rows:
        kind = 'Дохід' if r['kind']=='income' else 'Витрата'
        trs += f'<tr><td>{esc(r["day"])}</td><td><span class="badge {r["kind"]}">{kind}</span></td><td>{esc(r["category"])}</td><td>{esc(r["note"]) or "—"}</td><td class="num">{money(r["amount"])}</td><td class="actions"><a href="/?{urlencode({"month":month,"view":view,"day":day,"week":week,"edit":r["id"]})}#entry">Змінити</a><form method="post" action="/delete">{context_fields}<input type="hidden" name="csrf" value="{TOKEN}"><input type="hidden" name="month" value="{month}"><input type="hidden" name="id" value="{r["id"]}"><button class="delete" aria-label="Видалити операцію {r["id"]}" onclick="return confirm(\'Видалити цю операцію?\')">×</button></form></td></tr>'
    if not trs: trs = '<tr><td colspan="6" class="empty">За вибраний період операцій немає.</td></tr>' if first else '<tr><td colspan="6" class="empty">За цей місяць операцій немає.</td></tr>'
    css = STYLE
    return f"""<!doctype html><html lang="uk"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Кошти — фінансовий трекер</title><style>{css}</style></head><body><main>
    {navigation('home')}<header><div><div class="brand">◈ КОШТИ <span>ОСОБИСТИЙ ТРЕКЕР</span></div><h1>Фінанси під контролем</h1><p class="muted">Ваші гроші. Зрозуміла картина. Дані на вашому комп’ютері.</p></div><form method="get" class="filter"><label for="month">Період</label><input id="month" name="month" type="month" required value="{month}"><button>Показати</button></form></header>
    <section class="metrics" aria-label="Підсумки місяця"><article><p>Доходи за місяць</p><strong class="positive">{money(inc)}</strong></article><article><p>Витрати за місяць</p><strong>{money(exp)}</strong></article><article><p>Залишок за місяць</p><strong class="{'negative' if inc-exp<0 else 'positive'}">{money(inc-exp)}</strong><small>Доходи мінус витрати, не баланс рахунку</small></article></section>
    <section class="layout"><article class="panel" id="entry"><h2>{'Змінити операцію' if editing else 'Нова операція'}</h2>{f'<p role="alert" class="error">{esc(error)}</p>' if error else ''}<form method="post" action="/save" class="entry">{context_fields}<input type="hidden" name="csrf" value="{TOKEN}"><input type="hidden" name="month" value="{month}"><input type="hidden" name="id" value="{editing['id'] if editing else ''}"><label>Тип<select name="kind"><option value="expense" {'selected' if f['kind']=='expense' else ''}>Витрата</option><option value="income" {'selected' if f['kind']=='income' else ''}>Дохід</option></select></label><label>Сума, грн<input name="amount" type="number" min="0.01" max="100000000" step="0.01" placeholder="0,00" required value="{esc(f['amount'])}"></label><label>Категорія<select name="category">{options}</select></label><label>Дата<input name="day" type="date" required value="{esc(f['day'])}"></label><label>Опис<input name="note" maxlength="200" placeholder="Наприклад, покупки на тиждень" value="{esc(f['note'])}"></label><button class="primary">{'Зберегти зміни' if editing else '+ Додати операцію'}</button>{f'<a href="{esc(home_link(month,view,day,week))}">Скасувати редагування</a>' if editing else ''}</form></article><div class="chart-stack"><article class="panel"><h2>Топ-5 категорій витрат</h2><p class="muted category-caption">Суми та частки витрат за весь місяць</p>{bars}</article><article class="panel"><h2>Витрати протягом місяця</h2>{line}</article></div></section>
    <section class="panel history" id="history"><div class="section-heading"><h2>Історія операцій</h2><span class="muted">{len(rows)} із {len(month_all)} операцій · {month}</span></div>{selection_banner}<div class="table-scroll"><table><thead><tr><th>Дата</th><th>Тип</th><th>Категорія</th><th>Опис</th><th class="num">Сума</th><th>Дії</th></tr></thead><tbody>{trs}</tbody></table></div></section><footer>Python + SQLite · лише локальний доступ · валюта UAH</footer></main></body></html>"""


MONTH_NAMES = ('Січень','Лютий','Березень','Квітень','Травень','Червень','Липень','Серпень','Вересень','Жовтень','Листопад','Грудень')

def navigation(active):
    return '<nav class="tabs" aria-label="Основна навігація">' + ''.join(
        f'<a href="{url}" {"aria-current=page" if key == active else ""}>{label}</a>'
        for key,url,label in [('home','/','Огляд'),('archive','/archive','Архів')]) + '</nav>'

def archive_data(filters=None, today=None):
    # Read-only view of previous calendar months; existing schema is unchanged.
    filters = filters or {}; today = today or date.today()
    cutoff = today.replace(day=1).isoformat()
    with connect() as con:
        years = [r[0] for r in con.execute('SELECT DISTINCT substr(day,1,4) FROM transactions WHERE day < ? ORDER BY 1 DESC',(cutoff,))]
        year = str(filters.get('year') or (years[0] if years else today.year))
        if len(year)!=4 or not year.isascii() or not year.isdigit() or not 1<=int(year)<=9999:
            raise ValueError('Оберіть коректний рік.')
        month = str(filters.get('month') or '')
        if month and (not month.isascii() or not month.isdigit() or not 1<=int(month)<=12):
            raise ValueError('Оберіть коректний місяць.')
        month = f'{int(month):02}' if month else ''
        kind = filters.get('kind',''); category = filters.get('category',''); query = filters.get('q','').strip()
        if kind not in ('','income','expense') or category not in ('',)+CATEGORIES:
            raise ValueError('Некоректний тип або категорія.')
        if len(query)>200: raise ValueError('Пошуковий запит: максимум 200 символів.')
        try: requested_page=int(filters.get('page','1'))
        except (ValueError,TypeError): raise ValueError('Некоректна сторінка.')
        if requested_page<1: raise ValueError('Некоректна сторінка.')
        where=['day < ?','substr(day,1,4) = ?']; params=[cutoff,year]
        for column,value in [('substr(day,6,2)',month),('kind',kind),('category',category)]:
            if value: where.append(column+' = ?'); params.append(value)
        if query:
            # Literal substring search: % and _ are not wildcard operators.
            where.append('instr(casefold(note), casefold(?)) > 0'); params.append(query)
        condition=' AND '.join(where)
        summary=con.execute("SELECT count(*) AS total, COALESCE(SUM(CASE WHEN kind='income' THEN amount ELSE 0 END),0) AS income, COALESCE(SUM(CASE WHEN kind='expense' THEN amount ELSE 0 END),0) AS expense FROM transactions WHERE "+condition,params).fetchone()
        page_count=max(1,(summary['total']+49)//50); page=min(requested_page,page_count)
        rows=con.execute('SELECT * FROM transactions WHERE '+condition+' ORDER BY day DESC,id DESC LIMIT 50 OFFSET ?',params+[(page-1)*50]).fetchall()
    years=sorted(set(years+[year]),reverse=True)
    return {'rows':rows,'years':years,'year':year,'month':month,'kind':kind,'category':category,'q':query,'page':page,'pages':page_count,'total':summary['total'],'income':summary['income'],'expense':summary['expense'],'cutoff':cutoff}

def render_archive(filters=None, today=None):
    d=archive_data(filters,today); css=STYLE
    def options(items, selected):
        return ''.join(f'<option value="{esc(value)}" {"selected" if value==selected else ""}>{esc(label)}</option>' for value,label in items)
    year_opts=options([(y,y) for y in d['years']],d['year'])
    month_opts=options([('','Увесь рік')]+[(f'{i:02}',label) for i,label in enumerate(MONTH_NAMES,1)],d['month'])
    kind_opts=options([('','Усі типи'),('income','Доходи'),('expense','Витрати')],d['kind'])
    cat_opts=options([('','Усі категорії')]+[(c,c) for c in CATEGORIES],d['category'])
    period=f"{MONTH_NAMES[int(d['month'])-1]} {d['year']}" if d['month'] else d['year']
    trs=''
    for r in d['rows']:
        label='Дохід' if r['kind']=='income' else 'Витрата'
        link='/?'+urlencode({'month':r['day'][:7]})
        trs+=f'<tr><td>{esc(r["day"])}</td><td><span class="badge {r["kind"]}">{label}</span></td><td>{esc(r["category"])}</td><td>{esc(r["note"]) or "—"}</td><td class="num">{money(r["amount"])}</td><td><a class="month-link" href="{esc(link)}">Відкрити місяць</a></td></tr>'
    if not trs: trs='<tr><td colspan="6" class="empty">За обраними фільтрами минулих операцій немає. Змініть період або скиньте фільтри.</td></tr>'
    pagination=''
    for step,label in [(-1,'← Назад'),(1,'Далі →')]:
        target=d['page']+step
        if 1<=target<=d['pages']:
            args={k:d[k] for k in ('year','month','kind','category','q')};args['page']=target
            pagination+=f'<a href="/archive?{esc(urlencode(args))}">{label}</a>'
    balance=d['income']-d['expense']
    return f'''<!doctype html><html lang="uk"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Архів — Кошти</title><style>{css}</style></head><body><main>
    {navigation('archive')}<header class="archive-header"><div><div class="brand">◈ КОШТИ <span>ІСТОРІЯ ФІНАНСІВ</span></div><h1>Архів операцій</h1><p class="muted">Усі збережені операції до {esc(d['cutoff'])}. Поточний місяць — у розділі «Огляд».</p></div></header>
    <section class="panel archive-filters"><h2>Знайти минулі операції</h2><form action="/archive" method="get" class="archive-form"><label>Рік<select name="year">{year_opts}</select></label><label>Місяць<select name="month">{month_opts}</select></label><label>Тип<select name="kind">{kind_opts}</select></label><label>Категорія<select name="category">{cat_opts}</select></label><label class="search-field">Пошук в описі<input name="q" maxlength="200" placeholder="Наприклад, оренда" value="{esc(d['q'])}"></label><div class="filter-actions"><button class="primary">Застосувати</button><a href="/archive">Скинути</a></div></form></section>
    <p class="archive-caption muted">{esc(period)} · підсумки всіх операцій за вибраними фільтрами, не лише поточної сторінки</p>
    <section class="metrics" aria-label="Підсумки архівної вибірки"><article><p>Доходи</p><strong class="positive">{money(d['income'])}</strong></article><article><p>Витрати</p><strong>{money(d['expense'])}</strong></article><article><p>Доходи мінус витрати</p><strong class="{'negative' if balance<0 else 'positive'}">{money(balance)}</strong><small>Не баланс банківського рахунку</small></article></section>
    <section class="panel history"><div class="section-heading"><h2>Минулі операції</h2><span class="muted">Знайдено: {d['total']}</span></div><div class="table-scroll"><table><thead><tr><th>Дата</th><th>Тип</th><th>Категорія</th><th>Опис</th><th class="num">Сума</th><th>Перегляд</th></tr></thead><tbody>{trs}</tbody></table></div><div class="pagination"><span class="muted">Сторінка {d['page']} з {d['pages']} · до 50 записів</span><div>{pagination}</div></div></section>
    <footer>Архів лише для перегляду. Для змін відкрийте відповідний місяць. Архів — не резервна копія.</footer></main></body></html>'''

class Handler(BaseHTTPRequestHandler):
    def send_html(self, content, status=200):
        data = content.encode('utf-8'); self.send_response(status)
        self.send_header('Content-Type','text/html; charset=utf-8')
        self.send_header('Content-Length',str(len(data))); self.send_header('Cache-Control','no-store')
        self.send_header('X-Content-Type-Options','nosniff'); self.send_header('X-Frame-Options','DENY')
        self.end_headers(); self.wfile.write(data)
    def do_GET(self):
        parsed = urlparse(self.path)
        args = parse_qs(parsed.query)
        if parsed.path == '/archive':
            try: return self.send_html(render_archive({k:v[0] for k,v in args.items()}))
            except (ValueError, OverflowError): return self.send_html('Некоректні фільтри архіву. <a href="/archive">Скинути фільтри</a>',400)
        if parsed.path != '/': return self.send_html('Не знайдено',404)
        month = args.get('month',[date.today().strftime('%Y-%m')])[0]
        try: self.send_html(render(month, args.get('edit',[None])[0], view=args.get('view',['days'])[0], day=args.get('day',[''])[0], week=args.get('week',[''])[0]))
        except (ValueError, OverflowError): self.send_html('Некоректний місяць, режим графіка або фільтр дат. <a href="/">На головну</a>',400)
    def do_POST(self):
        if urlparse(self.path).path not in ('/save','/delete'): return self.send_html('Не знайдено',404)
        try:
            size = int(self.headers.get('Content-Length','0'))
            if size <= 0 or size > 16384: return self.send_html('Некоректний розмір запиту',413)
            form = {k:v[0] for k,v in parse_qs(self.rfile.read(size).decode('utf-8'),keep_blank_values=True).items()}
            if not secrets.compare_digest(form.get('csrf',''),TOKEN): return self.send_html('Перезавантажте сторінку та повторіть спробу.',403)
            month = form.get('month',date.today().strftime('%Y-%m')); month_dates(month)
            view, day, week = form.get('view','days'), form.get('filter_day',''), form.get('filter_week','')
            if view not in CHART_VIEWS: raise ValueError('Некоректний режим графіка.')
            history_selection(month, day, week)
            if urlparse(self.path).path == '/delete':
                with connect() as con: con.execute('DELETE FROM transactions WHERE id=?',(int(form['id']),))
            else:
                values = validate(form)
                with connect() as con:
                    if form.get('id'): con.execute('UPDATE transactions SET day=?,kind=?,category=?,amount=?,note=? WHERE id=?', values+(int(form['id']),))
                    else: con.execute('INSERT INTO transactions(day,kind,category,amount,note) VALUES (?,?,?,?,?)',values)
            self.send_response(303); self.send_header('Location',home_link(month, view, day, week)); self.end_headers()
        except (ValueError, KeyError, UnicodeError) as err:
            safe_month = date.today().strftime('%Y-%m')
            try: date.fromisoformat(form.get('month','')+'-01'); safe_month=form['month']
            except (ValueError, UnboundLocalError): pass
            self.send_html(render(safe_month,error=str(err),form=form if 'form' in locals() else None),400)

def seed():
    today = date.today(); month = today.strftime('%Y-%m')
    with connect() as con:
        if con.execute('SELECT count(*) FROM transactions').fetchone()[0]:
            print('Демо не додано: база вже містить операції.'); return
        for day, kind, cat, amount, note in [(1,'income','Зарплата',4200000,'Демонстраційні дані'),(2,'expense','Житло',1200000,'Оренда'),(3,'expense','Продукти',148050,'Продукти на тиждень'),(4,'expense','Транспорт',42000,'Проїзд'),(5,'expense','Розваги',75000,'Кіно та вечеря'),(6,'expense','Продукти',62000,'Закупи'),(7,'expense','Здоров’я',98000,'Аптека')]:
            con.execute('INSERT INTO transactions(day,kind,category,amount,note) VALUES (?,?,?,?,?)',(f'{month}-{day:02}',kind,cat,amount,note))
    print('Додано демонстраційні операції, це не ваші реальні фінанси.')
if __name__ == '__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--port',type=int,default=8000); parser.add_argument('--demo',action='store_true'); args=parser.parse_args()
    init_db()
    if args.demo: seed()
    server=ThreadingHTTPServer(('127.0.0.1',args.port),Handler)
    print(f'Відкрийте http://127.0.0.1:{args.port} · Ctrl+C для зупинки')
    try: server.serve_forever()
    except KeyboardInterrupt: pass
    finally: server.server_close()
