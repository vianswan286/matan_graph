import sqlite3
import re
from create_database import create_database

def extract_main_formula(text):
    """Извлекает самую длинную формулу из текста."""
    if not text:
        return None
    # Ищем формулы в разных форматах: $...$, \[...\], \begin{equation*}...\end{equation*}
    formulas = re.findall(r"""\$(.*?)\$|
                         \[(.*?)\]|
                         \\begin{equation\*}(.*?)\\end{equation\*}""",
                         text, re.DOTALL)
    
    # Уплощаем список и убираем пустые совпадения
    flat_formulas = [item.strip() for sublist in formulas for item in sublist if item and item.strip()]

    if not flat_formulas:
        return None
    
    # Возвращаем самую длинную формулу
    return max(flat_formulas, key=len)

# --- ДАННЫЕ ИЗ ЛЕКЦИЙ ---

definitions_data = [
    # --- Лекция 1 ---
    {"term_ru": "Бесконечное множество", "definition_ru": "Множество $A$ называется \\textit{бесконечным}, если оно эквивалентно своей правильной части. То есть $\\exists B \\subset A, B \\neq A$: $A \\sim B.$"},
    {"term_ru": "Декартово произведение", "definition_ru": "$X, Y \\neq \\varnothing.$ \\textit{Декартовым произведением} множеств $X$ и $Y$ называется множество упорядоченных пар $(x, y)$ таких, что $x \\in X, y \\in Y.$ Обозначение: $X \\times Y.$"},
    {"term_ru": "Соответствие f из X в Y", "definition_ru": "\\textit{Соответствием} $f$ из $X$ в $Y$ называется любое подмножество декартова произведения $X \\times Y.$ Обозначение: $f \\subset X \\times Y.$ $G_{f}$~---~график соответствия."},
    {"term_ru": "Область определения соответствия", "definition_ru": "$D_{f} := \\{ x \\in X: \\exists y \\in Y, (x,y) \\in G_{f} \\}.$ Множество всех первых элементов пар."},
    {"term_ru": "Область значений соответствия", "definition_ru": "$E_{f} := \\{ y \\in Y: \\exists x \\in X, (x,y) \\in G_{f} \\}.$ Множество всех вторых элементов пар."},
    {"term_ru": "Отображение (многозначное)", "definition_ru": "Если $D_{f} = X, $ то говорят, что задано отображение (многозначное) из $X$ в $Y$ $f$: $X \\mapsto Y.$"},
    {"term_ru": "Отображение (однозначное)", "definition_ru": "$X, Y \\neq \\varnothing$. Будем говорить, что $f$: $X \\mapsto Y$ --- \\textit{отображение}, если $D_{f} = X$ и $\\forall x \\in X$ $\\exists ! y \\in Y$: $(x,y) \\in G_{f}.$ Последнее можно интерпретировать как $y = f(x) .$ Если не сказано обратного, то отображение считать однозначным."},
    {"term_ru": "Композиция отображений", "definition_ru": "$X, Y, Z \\neq \\varnothing.$ $f$: $X \\mapsto Y,$ $y$: $Y \\mapsto Z$ --- отображения. \\textit{Композицией отображений} $f$ и $g$ назовём отображение $h = g \\circ f, $ если $h(x) = g(f(x)) \\quad \\forall x \\in X.$"},
    {"term_ru": "Инъекция", "definition_ru": "Отображение $f$: $X \\mapsto Y$ --- \\textit{инъекция}, если $\\forall x_{1}, x_{2} \\in X \\hookrightarrow x_{1} \\neq x_{2} \\Rightarrow f(x_{1}) \\neq f(x_{2}).$"},
    {"term_ru": "Сюръекция", "definition_ru": "Отображение $f$: $X \\mapsto Y$ --- \\textit{сюръекция}, если $E_{f} = Y.$ Каждый элемент множества $Y$ является образом хотя бы одного элемента множества $X.$"},
    {"term_ru": "Обратимое отображение", "definition_ru": "Отображение $f$: $X \\mapsto Y$ называется \\textit{обратимым}, если $\\exists f^{-1}$: $Y \\mapsto X,$ такое, что $f \\circ f^{-1} = Id_{Y}$ и $f^{-1} \\circ f = Id_{X}$ при этом $f^{-1}$ называется обратной к $f$."},
    {"term_ru": "Множество действительных чисел", "definition_ru": "\\textit{Множеством действительных чисел} называется непустое множество $\\R$, в котором введены 2 бинарные операции: <<+>>: $\\R^{2} \\mapsto \\R$ и <<$\\cdot$>>: $\\R^{2} \\mapsto \\R$, и отношение порядка \"$\\leq$\". Удовлетворяют 15 аксиомам."},
    {"term_ru": "Аксиома непрерывности", "definition_ru": "\\textit{Аксиома непрерывности.} $\\forall A, B \\subset \\R: A, B \\neq \\varnothing$ и $\\forall a \\in A, \\forall b \\in B \\hookrightarrow a \\leq b.$ $\\exists c \\in \\R$: $a \\leq c \\leq b.$ То есть существует <<разделительное число>>."},
    {"term_ru": "Расширенное множество действительных чисел", "definition_ru": "$\\overline{\\R} := \\R \\cup \\{ -\\infty \\} \\cup \\{ +\\infty \\}.$ Притом $\\forall x \\in \\overline{\\R} \\neq \\pm \\infty \\hookrightarrow -\\infty < x < +\\infty.$"},
    {"term_ru": "Множество натуральных чисел с нулем", "definition_ru": "$\\N_{0} := \\N \\cup \\{ 0 \\}.$"},
    {"term_ru": "Отрезок", "definition_ru": "$[a, b] := \\{x \\in \\R$: $a \\leq x \\leq b \\}.$"},
    {"term_ru": "Интервал", "definition_ru": "$(a, b) := \\{x \\in \\R$: $a < x < b \\}.$"},
    {"term_ru": "Ограниченное сверху множество", "definition_ru": "Множество $A \\subset \\R$ называется \\textit{ограниченным сверху}, если $\\exists M \\in \\R$: $a \\leq M \\quad \\forall a \\in A.$"},
    {"term_ru": "Ограниченное снизу множество", "definition_ru": "Множество $A \\subset \\R$ называется \\textit{ограниченным снизу}, если $\\exists m \\in \\R$: $m \\leq a  \\quad \\forall a \\in A.$"},
    {"term_ru": "Ограниченное множество", "definition_ru": "Множество $A \\subset \\R$ называется \\textit{ограниченным}, если оно ограниченно и сверху, и снизу."},
    # --- Лекция 2 ---
    {"term_ru": "Верхняя (нижняя) грань", "definition_ru": "Число $M (m)$ называется \\textit{верхней (нижней) гранью} числового непустого множества $A \\subset \\R,$ если $x \\leq M$ ($x \\geq m$) $\\quad \\forall x \\in A.$"},
    {"term_ru": "Супремум", "definition_ru": "Пусть $A$~---~ограниченное сверху множество. Число $M \\in \\R$ называется супремумом $A$ и записывается $M = sup A$, если выполняется: 1. $M$ является верхней гранью, то есть $\\forall x \\in A \\hookrightarrow x \\leq M$. 2. $\\forall M^{'} < M \\quad \\exists a(M^{'}) \\in A$: $M^{'} < a(M^{'}) \\leq M.$"},
    {"term_ru": "Супремум неограниченного множества", "definition_ru": "Если $A$~---~неограниченное сверху множество, то $sup A := +\\infty.$"},
    {"term_ru": "Инфимум", "definition_ru": "$m \\in \\R$ называется \\textit{инфимумом ограниченного снизу множества} $A$, если $m = \\inf{A} \\Longleftrightarrow \\begin{cases} a \\geq m \\quad \\forall a \\in A\\\\ \\forall m^{'} > m, \\  \\exists a(m^{'}) \\in A: m^{'} > a(m^{'}) \\geq m& \\end{cases}$"},
    {"term_ru": "Инфимум неограниченного множества", "definition_ru": "Если $A$~---~неограниченное снизу множество, то $\\inf{A} := -\\infty.$"},
    {"term_ru": "Максимум (минимум)", "definition_ru": "Число $M$ называется \\textit{максимумом (максимальным элементом)} множества $E \\subset \\R \\Leftrightarrow M = max E$, если 1. $M \\in E$; 2. $M \\geq x \\  \\forall x \\in E.$ Аналогично определяется минимум."},
    {"term_ru": "Последовательность отрезков", "definition_ru": "Отображение из $\\N$ в множество всех отрезков на числовой прямой $\\R$ назовём \\textit{последовательностью отрезков} и обозначим $\{ [a_{n}, b_{n}] \\}^{\\infty}_{n = 1}$"},
    {"term_ru": "Последовательность вложенных отрезков", "definition_ru": "Будем говорить, что $\{ [a_{n}, b_{n}] \\}^{\\infty}_{n = 1}$~---~последовательность \\textit{вложенных отрезков}, если $\{ [a_{n+1}, b_{n+1}] \} \\subset \{ [a_{n}, b_{n}] \} \\quad \\forall n \\in \\N$"},
    {"term_ru": "Стягивающаяся последовательность отрезков", "definition_ru": "Последовательность вложенных отрезков $\\displaystyle \\bigcap_{n = 1}^{\\infty} [a_{n}, b_{n}]$ называется \\textit{стягивающейся}, если $\\forall n \\in \\N \\  \\exists [a_{m(n)}, b_{m(n)}]$: $l \\displaystyle < \\frac{1}{n}$, где $l = (b_{i} - a_{i})$. $l$~---~длина."},
]

theorems_data = [
    # --- Лекция 1 ---
    {"name_ru": "Несправедливость аксиомы непрерывности для рациональных чисел", "statement_ru": "Аксиома непрерывности не справедлива для рациональных чисел ($\\Q$).", "proof_ru": "Предположим, что $\\Q$ удовлетворяет аксиоме непрерывности. $A := \\{ x \\in \\Q: x \\geq 0, x^2 < 2\\}$, $B := \\{ x \\in \\Q: x^2 > 2 \\}$. Если аксиомa непрерывности верна для $\\Q$, то это означает, что $\\exists c \\in \\Q: \\forall a \\in A, \\forall b \\in B \\hookrightarrow a \\leq c \\leq b$. Возьмём наши множества $A, B$, тогда $c^2 = 2,$ но $! \\exists c \\in \\Q: c^2 = 2 \\Rightarrow$ противоречие."},
    # --- Лекция 2 ---
    {"name_ru": "Теорема о существовании и единственности супремума", "statement_ru": "Супремум существует и единственен. $$\\forall A \\subset \\R: A \\neq \\varnothing \\hookrightarrow \\exists! \\sup{A}.$$", "proof_ru": "В случае неограниченного множества $A$ верность теоремы следует из определения. Рассмотрим случай ограниченного множества $A \\Rightarrow$ существует хотя бы одна верхняя грань. Пусть $B := \\{M \\in \\R: M - \\text{верния грань } A\\}. \\quad B \\neq \\varnothing .$ Кроме того $A$ расположенно левее $B$. Тогда в силу аксиомы непрерывности $\\exists c \\in \\R$: $a \\leq c \\leq M \\quad \\forall a \\in A, \\quad \\forall M \\in B.$ Покажем, что $c = \\sup{A}.$ Действительно, так как $a \\leq c \\ \\forall a \\in A \\Rightarrow c$~---~верхняя грань, тогда 1 пункт определния супремума проверен. Предположим $\\exists c' < c$: $c'$~---~верхняя грань. Тогда $c' \\in B$, но $c$ было выбранно так, что $c \\leq M \\quad \\forall M \\in B \\Rightarrow c \\leq c'$~---~противоречие $\\Rightarrow \\forall c' < c \\hookrightarrow c \\notin B \\Leftrightarrow \\lnot (c' \\in B) \\Leftrightarrow \\lnot (\\forall a \\in A \\hookrightarrow a \\leq c') \\Leftrightarrow \\exists a(c') \\in A: a(c') > c'$, но так как $a(c') \\in A$, то $a(c') \\leq c.$ И тогда мы показали, что $\\forall c' < c \\quad \\exists a(c^{'}) \\in A$: $c' < a(c^{'}) \\leq c.$ Значит, мы проверили определние супремума с заменой $M$ на $c \\Rightarrow$ он существует. Докажем единственность супремума. Предположим, что $\\exists M_{1}, M_{2} \\in \\R$: $M_{1} = \\sup{A}$ и $M_{2} = \\sup{A}.$ Пусть $M_{1} > M_{2}.$ Тогда по (2) пункту определения супремума (для $M_{1}$) $\\exists a(M_{2}) \\in A$: $a(M_{2}) > M_{2} \\Rightarrow$ это противоречит тому, что $M_{2}$~---~верхняя грань (то есть (1) пункт определения $M_{2}$ как супремума) $\\Rightarrow$ такого быть не может. Случай $M_{2} > M_{1}$ аналогичен $\\Rightarrow M_{1} = M_{2},$ то есть супремум существует и единственнен."},
    {"name_ru": "Утверждение о супремуме", "statement_ru": "$M = \\sup{A} \\text{  } (M \\in \\overline{\\R}, \\  A \\subset \\R, \\  A \\neq \\varnothing$) тогда и только тогда, когда $\\begin{cases} a \\leq M \\quad \\forall a \\in A\\\\ \\forall M^{'} < M \\  \\exists a(M^{'}) \\in A: M^{'} < a(M^{'}) \\leq M& \\end{cases}$"},
    {"name_ru": "Лемма Архимеда", "statement_ru": "Множество натуральных чисел неограниченно сверху. $$\\forall M^{'} \\in \\R \\text{  } \\exists N (M^{'}) \\in \\N: N (M^{'}) > M^{'}.$$", "proof_ru": "Предположим, что $\\N$~---~ограниченно сверху $\\Rightarrow$ существует верхняя грань и более того существует конечный супремум $M = \\sup{\\N} < +\\infty.$ Тогда в силу второго пункта определения супрерума: $\\forall M^{'} < M$ найдётся натуральное число его больше. Но так как это верно $\\forall M^{'}$, то можем взять $M^{'} = M - 1. \\newline$ Тогда $\\exists N(M^{'}) \\in \\N$: $N(M^{'}) > M - 1 \\Rightarrow N(M^{'}) + 1 > M \\Rightarrow M$~---~не супремум. Противоречие."},
    {"name_ru": "Теорема о существовании и единственности инфимума", "statement_ru": "Инфимум существует и единственен. $$\\forall A \\subset \\R: A \\neq \\varnothing \\hookrightarrow \\exists! \\inf{A}.$$", "proof_ru": "Аналогично супремуму с точностью до замены знаков."},
    {"name_ru": "Утверждение об инфимуме", "statement_ru": "$m = \\inf{A} \\text{  } (m \\in \\overline{\\R}, \\  A \\subset \\R, \\  A \\neq \\varnothing$) тогда и только тогда, когда $\\begin{cases} a \\geq m \\quad \\forall a \\in A\\\\ \\forall m^{'} > m \\  \\exists a(m^{'}) \\in A: m^{'} > a(m^{'}) \\geq m& \\end{cases}$"},
    {"name_ru": "Лемма Кантора о вложенных отрезках", "statement_ru": "Любая последовательность вложенных отрезков имеет непустое пересечение (точка лежит сразу во всех отрезках), то есть $$\\forall \\text{ вложенной } \\{ [a_{n}, b_{n}] \\}^{\\infty}_{n = 1} \\quad \\exists x \\in \\bigcap_{n = 1}^{\\infty} [a_{n}, b_{n}] \\Longleftrightarrow \\bigcap_{n = 1}^{\\infty} [a_{n}, b_{n}] \\neq \\varnothing$$", "proof_ru": "$\\forall n \\in \\N$ справедливы неравенства: $-\\infty < a_{n} \\leq a_{n+1} \\leq b_{n+1} \\leq b_{n} < +\\infty.$ Заметим следующий факт (*): $ \\forall n, m \\in \\N \\hookrightarrow -\\infty < a_{n} \\leq b_{m} < +\\infty$. $A := \\{a_{1}, a_{2} \\dots , a_{n}, \\dots \\}$~---~ множество «левых» концов. $B := \\{b_{1}, b_{2} \\dots , b_{m}, \\dots \\}$~---~множество «правых» концов. Из (*) получаем, что $A$ расположенно «левее» $B \\Rightarrow \\exists c \\in \\R$: $a_{n} \\leq c \\leq b_{m} \\  \\forall n, m \\in \\N \\Rightarrow \\newline \\Rightarrow a_{n} \\leq c \\leq b_{n} \\quad \\forall n \\in \\N \\Rightarrow c \\in [a_{n}, b_{n}] \\  \\forall n \\in \\N \\Rightarrow c \\in \\displaystyle \\bigcap_{n = 1}^{\\infty} [a_{n}, b_{n}]$"},
    {"name_ru": "Теорема о стягивающейся последовательности", "statement_ru": "Стягивающаяся последовательность вложенных отрезков $\{ [a_{n}, b_{n}] \\}^{\\infty}_{n = 1}$ имеет единственную общую точку, то есть $$ \\exists ! x \\in \\bigcap_{n = 1}^{\\infty} [a_{n}, b_{n}]$$", "proof_ru": "Ранее было доказано, что пересечение не пусто. Тогда предположим, что $\\displaystyle \\exists x_{1}, x_{2} \\in \\bigcap_{n = 1}^{\\infty} [a_{n}, b_{n}] \\quad (x_{1} \\neq x_{2}).$ Так как $x_{1} \\neq x_{2} \\Rightarrow |x_{1} - x_{2}| > 0.$ Пусть $\\displaystyle |x_{1} - x_{2}| = \\frac{1}{M}.$ Но тогда по лемме Архимеда $\\displaystyle \\exists N \\in \\N$: $\\displaystyle N > M \\Rightarrow \\frac{1}{N} < |x_{1} - x_{2}| \\Rightarrow$ в силу того, что система отрезков стягивающаяся, то $\\exists [a_{m(N)}, b_{m(N)}]$ длина которого $\\displaystyle < \\frac{1}{N}$, но по предположению $x_{1}, x_{2}$ принадлежат всем отрезкам этой последовательности, в частности $\\displaystyle x_{1}, x_{2} \\in [a_{m(N)}, b_{m(N)}] \\Rightarrow |x_{1} - x_{2}| < \\frac{1}{N} \\Rightarrow |x_{1} - x_{2}| < |x_{1} - x_{2}|$~---~ противоречие. Получается $x_{1} = x_{2}.$"},
    {"name_ru": "Теорема о 3 принципах непрерывности", "statement_ru": "Следующие утверждения эквивалентны: 1. Аксиома непрерывности. 2. Существование $\\inf$ и $\\sup$ у любого непустого множества. 3. Лемма Кантора о непустоте пересечения вложенной системы и лемма Архимеда."}
]

# --- СТРУКТУРА СВЯЗЕЙ ---
# Ключ - название теоремы. Значение - словарь с двумя списками:
# 'defs' - определения, на которые ссылается теорема
# 'theorems' - другие теоремы/леммы, на которые она ссылается
definition_links_data = {
    "Соответствие f из X в Y": ["Декартово произведение"],
    "Область определения соответствия": ["Соответствие f из X в Y"],
    "Область значений соответствия": ["Соответствие f из X в Y"],
    "Отображение (многозначное)": ["Область определения соответствия"],
    "Отображение (однозначное)": ["Отображение (многозначное)"],
    "Композиция отображений": ["Отображение (однозначное)"],
    "Инъекция": ["Отображение (однозначное)"],
    "Сюръекция": ["Отображение (однозначное)", "Область значений соответствия"],
    "Обратимое отображение": ["Отображение (однозначное)", "Композиция отображений"],
    "Ограниченное множество": ["Ограниченное сверху множество", "Ограниченное снизу множество"],
    "Верхняя (нижняя) грань": ["Ограниченное сверху множество", "Ограниченное снизу множество"],
    "Супремум": ["Ограниченное сверху множество", "Верхняя (нижняя) грань"],
    "Инфимум": ["Ограниченное снизу множество", "Верхняя (нижняя) грань"],
    "Последовательность вложенных отрезков": ["Последовательность отрезков"],
    "Стягивающаяся последовательность отрезков": ["Последовательность вложенных отрезков"],
}

links_data = {
    "Несправедливость аксиомы непрерывности для рациональных чисел": {
        "defs": ["Аксиома непрерывности", "Ограниченное сверху множество", "Ограниченное снизу множество"],
        "theorems": []
    },
    "Теорема о существовании и единственности супремума": {
        "defs": ["Супремум", "Верхняя (нижняя) грань", "Ограниченное сверху множество", "Аксиома непрерывности"],
        "theorems": []
    },
    "Лемма Архимеда": {
        "defs": ["Ограниченное сверху множество", "Супремум"],
        "theorems": []
    },
    "Теорема о существовании и единственности инфимума": {
        "defs": ["Инфимум", "Верхняя (нижняя) грань"],
        "theorems": ["Теорема о существовании и единственности супремума"] # т.к. док-во аналогично
    },
    "Лемма Кантора о вложенных отрезках": {
        "defs": ["Последовательность вложенных отрезков", "Аксиома непрерывности", "Отрезок"],
        "theorems": []
    },
    "Теорема о стягивающейся последовательности": {
        "defs": ["Стягивающаяся последовательность отрезков"],
        "theorems": ["Лемма Архимеда", "Лемма Кантора о вложенных отрезках"]
    },
    "Теорема о 3 принципах непрерывности": {
        "defs": ["Аксиома непрерывности"],
        "theorems": ["Теорема о существовании и единственности супремума", "Теорема о существовании и единственности инфимума", "Лемма Кантора о вложенных отрезках", "Лемма Архимеда"]
    }
}

# --- ЛОГИКА ЗАГРУЗКИ В БД ---

def load_data(db_name='math_base.db'):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    definitions_map = {}
    theorems_map = {}

    print("--- Загрузка определений ---")
    for item in definitions_data:
        term_ru = item['term_ru']
        definition_ru = item['definition_ru']
        formula = extract_main_formula(definition_ru)
        
        cursor.execute("SELECT id FROM definitions WHERE term_ru = ?", (term_ru,))
        existing_def = cursor.fetchone()

        if existing_def:
            item_id = existing_def[0]
            print(f"Определение '{term_ru}' уже существует (ID: {item_id}). Пропускаем.")
        else:
            cursor.execute("INSERT INTO definitions (term_ru, definition_ru, formula) VALUES (?, ?, ?)",
                           (term_ru, definition_ru, formula))
            item_id = cursor.lastrowid
            print(f"Добавлено определение: '{term_ru}' (ID: {item_id})")
        
        definitions_map[term_ru] = item_id

    print("\n--- Загрузка теорем ---")
    for item in theorems_data:
        name_ru = item['name_ru']
        statement_ru = item['statement_ru']
        proof_ru = item.get('proof_ru')
        formula = extract_main_formula(statement_ru)

        cursor.execute("SELECT id FROM theorems WHERE name_ru = ?", (name_ru,))
        existing_theorem = cursor.fetchone()

        if existing_theorem:
            item_id = existing_theorem[0]
            print(f"Теорема '{name_ru}' уже существует (ID: {item_id}). Пропускаем.")
        else:
            cursor.execute("INSERT INTO theorems (name_ru, statement_ru, proof_ru, formula) VALUES (?, ?, ?, ?)",
                           (name_ru, statement_ru, proof_ru, formula))
            item_id = cursor.lastrowid
            print(f"Добавлена теорема: '{name_ru}' (ID: {item_id})")
        
        theorems_map[name_ru] = item_id
            
    # --- Создание связей ---
    print("\n--- Создание связей ---")
    for theorem_name, links in links_data.items():
        theorem_id = theorems_map.get(theorem_name)
        if not theorem_id:
            print(f"ПРЕДУПРЕЖДЕНИЕ: Не найдена теорема '{theorem_name}' для создания связей.")
            continue

        # Связи с определениями
        for def_name in links.get("defs", []):
            definition_id = definitions_map.get(def_name)
            if definition_id:
                cursor.execute("INSERT OR IGNORE INTO theorem_uses_definition (theorem_id, definition_id, context) VALUES (?, ?, 'proof')",
                               (theorem_id, definition_id))
                if cursor.rowcount > 0:
                    print(f"Создана связь: Теорема '{theorem_name}' -> Определение '{def_name}'")
            else:
                print(f"ПРЕДУПРЕЖДЕНИЕ: Не найдено определение '{def_name}' для связи с теоремой '{theorem_name}'.")

        # Связи с другими теоремами
        for used_theorem_name in links.get("theorems", []):
            used_theorem_id = theorems_map.get(used_theorem_name)
            if used_theorem_id:
                cursor.execute("INSERT OR IGNORE INTO theorem_uses_theorem (theorem_id, used_theorem_id, context) VALUES (?, ?, 'proof')",
                               (theorem_id, used_theorem_id))
                if cursor.rowcount > 0:
                    print(f"Создана связь: Теорема '{theorem_name}' -> Теорема '{used_theorem_name}'")
            else:
                print(f"ПРЕДУПРЕЖДЕНИЕ: Не найдена теорема '{used_theorem_name}' для связи с теоремой '{theorem_name}'.")

    # --- Создание связей между определениями ---
    print("\n--- Создание связей между определениями ---")
    for definition_name, used_definitions in definition_links_data.items():
        definition_id = definitions_map.get(definition_name)
        if not definition_id:
            print(f"ПРЕДУПРЕЖДЕНИЕ: Не найдено определение '{definition_name}' для создания связей.")
            continue

        for used_definition_name in used_definitions:
            used_definition_id = definitions_map.get(used_definition_name)
            if used_definition_id:
                cursor.execute("INSERT OR IGNORE INTO definition_uses_definition (definition_id, used_definition_id) VALUES (?, ?)",
                               (definition_id, used_definition_id))
                if cursor.rowcount > 0:
                    print(f"Создана связь: Определение '{definition_name}' -> Определение '{used_definition_name}'")
            else:
                print(f"ПРЕДУПРЕЖДЕНИЕ: Не найдено определение '{used_definition_name}' для связи с определением '{definition_name}'.")

    conn.commit()
    conn.close()
    print("\nЗагрузка данных завершена.")

if __name__ == '__main__':
    # Сначала создаем/проверяем структуру БД
    create_database()
    # Затем загружаем данные
    load_data()
