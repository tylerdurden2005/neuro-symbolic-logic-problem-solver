from openai import OpenAI
from module1.config import Config


class Proofer:
    def __init__(self):
        self.config = Config()
        self.client = OpenAI(api_key=self.config.OPENAI_API_KEY)
        self.system_prompt = self.promt_create()

    def promt_create(self):
        return (
            """Ты — учитель логики. Твоя задача — кратко пояснять журнал доказательства, не добавляя никаких рассуждений сверх того, что уже содержится в шагах.

Стиль объяснения:

Пиши очень кратко, без подробностей и без переформулирования преобразований.

Не описывай, как были получены формулы — только фиксируй факт результата шага.

Каждый шаг должен быть оформлен так:
«Шаг N — <тип операции>. Результат:»
затем перечисление формул «в столбик», если их несколько.

Не добавляй новую информацию и не раскрывай ход преобразований.

Не более 2–3 предложений на шаг.

В начале ответа напомни, что предпосылки уже даны в журнале (если они есть), но не переписывай их.

В конце — краткое резюме в 2–3 предложения:
какие группы формул были получены (например: ПНФ получена, Сколемизация завершена) и что это означает в контексте дальнейшей резолюции (готово к превращению в клаузы).

Не используй LaTeX и сложное форматирование.

Пример желаемого формата шага:

Шаг 1 — Приведение формул к предваренной нормальной форме. Результат:

<формула>

<формула>

<формула>

Шаг 2 — Сколемизация. Результат:

<формула>

<формула>

И так далее.

Не используй никаких мета-комментариев или рассуждений вне шагов. Пиши только итоговые факты по каждому шагу журнала.
"""
        )

    def explain(self, proof: str):
        user_text = self.build_user_message(proof)
        return self.call_proofs(user_text)

    def build_user_message(self, proof):
        header = "Ниже приведён журнал доказательства. Объясни его по шагам простым русским языком.\n\n"

        if isinstance(proof, str):
            return header + proof.strip()

        if isinstance(proof, list):
            return header + "\n".join(map(str, proof))

        return header + str(proof)

    def call_proofs(self, text: str):
        try:
            resp = self.client.chat.completions.create(
                model=self.config.MODEL_NAME,
                messages=[{"role": "system", "content": self.system_prompt},{"role": "user", "content": text}]
            )
        except Exception as e:
            raise Exception(f"Ошибка при вызове OpenAI API: {e}")

        return resp.choices[0].message.content.strip()