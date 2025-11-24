import requests
import json
import traceback
from logger import PrettyLogger
from config import SERVER_URL

logger = PrettyLogger("mylogger")

def send_request_to_llama_server(
    system_prompt,
    user_prompt=None,
    json_mode=False,
    server_url=SERVER_URL,
    schema=None,
    max_tokens=6000,
    temperature=0.7,
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
        "model": "llama-model",
        "messages": history,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "max_new_tokens": 2000,
        "stream": True
    }

    if json_mode and schema is not None:
        payload["json_schema"] = schema

    headers = {
        "Content-Type": "application/json"
    }

    try:
        logger.info(f"Sending request to {server_url}")
        while True:
            try:
                with requests.post(server_url, headers=headers, json=payload, stream=True, timeout=(180, 300)) as response:
                    logger.info(f"Received response with status code: {response.status_code}")

                    if response.status_code == 200:
                        answer_text = ""
                        for line in response.iter_lines():
                            if line:
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
                                            if content is not None:
                                                answer_text += content
                                                print(content, end="", flush=True)
                                    except json.JSONDecodeError:
                                        # игнорируем невалидные строки
                                        continue

                        # Преобразуем в dict если требуется
                        if json_mode:
                            try:
                                return json.loads(answer_text)
                            except json.JSONDecodeError:
                                logger.error(f"Не удалось разобрать JSON: {answer_text}")
                                return {}
                        else:
                            return answer_text
                    else:
                        error_message = f"Request failed with status code {response.status_code}: {response.text}"
                        logger.error(error_message)
                        return error_message

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
