
from openai import OpenAI
from module1.config import Config

class TextFormalizer:
    def __init__(self):
        self.config = Config()
        self.client = OpenAI(api_key=self.config.OPENAI_API_KEY)
        self.system_prompt = self.create_system_prompt()

    def create_system_prompt(self):
        # Создание промта
        return """Ты — эксперт по формальной логике и компьютерной лингвистике.
ТВОЯ ЗАДАЧА:
Преобразовать входной текст на естественном языке в набор корректных и непротиворечивых формул логики предикатов первого порядка.

ВАЖНО:
Отвечай строго в требуемом формате.
Не раскрывай ход рассуждений.
Не используй формат thinking.
Не пиши ничего, кроме итогового ответа.

ФОРМАТ ОТВЕТА (обязателен):
Словарь предикатов и констант:
<список предикатов и констант с объяснениями>

Формулы:
<ровно одна формула на каждое предложение входного текста>
Не нужно нумеровать формулы!
Формулу, которую нужно доказать, писать всегда последней.
Перед формулой, которую нужно доказать, в начале приписывай отрицание: '¬', а саму формулу бери в скобки.


ПРАВИЛА:

Предикаты: создай отдельный предикат для каждого отношения или свойства. Укажи его значение на естественном языке.
Примеры:
Студент[x] — "x является студентом"
Любит[x,y] — "x любит y"

Константы: для имён собственных и уникальных объектов используй константы.
Пример:
anna — "Анна"

Используй кванторы ∀ и ∃.

Следи за областью действия кванторов.

Для аргументов предикатов используй квадратные скобки [], для остальных — круглые.

Используй логические связки: ∧, ∨, ¬, →, ≡.

Не добавляй ничего, что не следует явно из текста.

Количество формул должно быть равно количеству предложений (разделённых точкой).

Все переменные-аргументы должны заменяться на латинские буквы только из списка: x, y, z, u, w, v, t по порядку появления. 
Если свободных букв из списка не осталось, используй индексацию с 1: x1, y1, и так далее.
Это касается любых переменных (кванторных и свободных).

ПРИМЕР 1
Вход:
"Сократ человек. Все люди смертны."

Выход:
Словарь предикатов и констант:
Человек[x] – x является человеком
Смертен[x] – x является смертным
sokrat – Сократ

Формулы:
Человек[x]
∀x (Человек[x] → Смертен[x])

ПРИМЕР 2
Вход:
"Каждое чётное натуральное число является суммой двух простых чисел."
        
Выход:
Словарь предикатов и констант:
Натуральное[x] - x является натуральным числом
Четное[x] - x является чётным числом
Простое[x] - x является простым числом
Сумма[x,y,z] - z является суммой x и y
        
Формулы:
∀x ((Натуральное[x] ∧ Четное[x]) → ∃y ∃z (Простое[y] ∧ Простое[z] ∧ Сумма[y,z,x]))

Теперь формализуй данное выражение.
Отвечай только итоговым формализованным выводом."""


    def formalize_text(self, text: str):
        user_prompt = f'Текст: "{text}"'
        try:
            # Вызов OpenAI
            resp = self.client.chat.completions.create(
                model=self.config.MODEL_NAME,
                messages=[ {"role": "system", "content": self.system_prompt},{"role": "user", "content": user_prompt}]
            )
            # Извлечение текстового ответа из модели
            raw_response = resp.choices[0].message.content.strip()
            # Текст парсится на формулы и словарь предикатов
            predicates, formulas = self.parse_response(raw_response)
            return {
                "raw_response": raw_response,
                "predicates": predicates,
                "formulas": formulas
            }
        except Exception as e:
            raise Exception(f"Ошибка при вызове OpenAI API: {e}")

    def parse_response(self, response: str):
        # Текст парсится на формулы и словарь предикатов
        cleaned_response = response.strip()
        predicates = []
        formulas = []
        current_section = None
        lines = cleaned_response.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if "Словарь предикатов" in line:
                current_section = "predicates"
                continue
            elif "Формулы:" in line:
                current_section = "formulas"
                continue
            if current_section == "predicates":
                if ' - ' in line or ' — ' in line:
                    predicates.append(line)
            elif current_section == "formulas":
                if any(c in line for c in ['∀', '∃', '∧', '∨', '→', '¬', '[', ']', '(', ')', '≡']):
                    formulas.append(line)
        return predicates, formulas


