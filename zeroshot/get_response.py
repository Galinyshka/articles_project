import requests
import json
import traceback
import re
import string
from logger import PrettyLogger
from config import SERVER_URL, MODEL_NAME

logger = PrettyLogger("mylogger")


def send_request_to_llama_server(
    system_prompt,
    user_prompt=None,
    json_mode=False,
    server_url=SERVER_URL,
    schema=None,
    max_tokens=6000,
    temperature=0.9,
    history=None
):
    if history is None or not history:
        history = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    else:
        if history and history[0]['role'] != "system":
            history = [{"role": "system", "content": system_prompt}] + history

    payload = {
        "model": MODEL_NAME,
        "messages": history,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "max_new_tokens": 2048,
        "stream": True,
    }

    if json_mode and schema is not None:
        payload["extra_body"] = {"guided_json": schema}

    headers = {"Content-Type": "application/json"}

    try:
        logger.info(f"Sending request to {server_url}")
        while True:
            try:
                with requests.post(server_url, headers=headers, json=payload, stream=True, timeout=(180, 300)) as response:
                    logger.info(f"Received response with status code: {response.status_code}")

                    if response.status_code != 200:
                        error_message = f"Request failed with status code {response.status_code}: {response.text}"
                        logger.error(error_message)
                        return error_message

                    answer_text = ""
                    for line in response.iter_lines():
                        if not line:
                            continue
                        decoded_line = line.decode("utf-8")
                        if decoded_line.startswith("data: "):
                            json_data = decoded_line[len("data: "):]
                            if json_data.strip() == "[DONE]":
                                continue  # игнорируем конец потока
                            try:
                                data = json.loads(json_data)
                                choices = data.get("choices", [])
                                for choice in choices:
                                    delta = choice.get("delta", {})
                                    content = delta.get("content", "")
                                    if content:
                                        answer_text += content
                                        print(content, end="", flush=True)
                            except json.JSONDecodeError:
                                # игнорируем невалидные строки
                                continue

                    # Попытка распарсить JSON
                    if json_mode:
                        try:
                            return json.loads(answer_text)
                        except json.JSONDecodeError:
                            logger.error(f"Не удалось разобрать JSON, пробуем извлечь текстовое поле: {answer_text}")

                            # Ищем первое вхождение слова "class" до первой запятой
                            match = re.search(r"\bclass\b(.*?)(,|$)", answer_text, flags=re.IGNORECASE | re.DOTALL)
                            if match:
                                class_text = match.group(1).strip()
                                # Убираем все знаки препинания
                                class_text = class_text.translate(str.maketrans('', '', string.punctuation))
                                class_text = class_text.strip()
                                return {"class": class_text}
                            else:
                                logger.error("Не удалось найти слово 'class' в ответе")
                                return {"class": None}
                    else:
                        return answer_text

            except KeyboardInterrupt:
                raise KeyboardInterrupt()
            except Exception as e:
                logger.error(f"{e=}, продолжаем...")
                traceback.print_exc()
                continue

    except requests.exceptions.RequestException as e:
        error_message = f"Произошла ошибка запроса: {e}"
        logger.error(error_message)
        return error_message
