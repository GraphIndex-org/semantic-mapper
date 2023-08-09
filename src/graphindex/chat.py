import openai

from src.graphindex.common.prompts import CHAT_SYSTEM_PROMPT, CHAT_QUESTION_PROMPT


class GraphIndexBot:
    def __init__(self, openai_model="gpt-3.5-turbo-16k"):
        self.openai_model = openai_model
        self.system_prompt = CHAT_SYSTEM_PROMPT
        self.history = {}

    def chat(self, project_id, question, table_data, mapping, description=None):
        if project_id not in self.history:
            self.history[project_id] = [{"role": "system", "content": CHAT_SYSTEM_PROMPT}]

        history = self.history[project_id]

        description = description if description is not None else "No description."

        prompt = CHAT_QUESTION_PROMPT.format(
            table_data=table_data,
            mapping=mapping,
            description=description,
            question=question
        )

        history.append({"role": "user", "content": prompt})

        prompt_context = [history[0]] + history[-3:]

        chat = openai.ChatCompletion.create(
            model=self.openai_model,
            messages=prompt_context,
            temperature=0,
        )
        reply = chat.choices[0].message.content
        history.append({"role": "assistant", "content": reply})

        return reply
