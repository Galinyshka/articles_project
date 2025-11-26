from get_response import send_request_to_llama_server
import json 
import gc
import os 
from formatter import render_template
from logger import logger

TEST_ROOT = 'zeroshot/data/test/'
TRAIN_ROOT = 'zeroshot/data/train/'

def request_validation():
    system_template_name = "system.txt"
    user_template_name = "user.txt"
    system_message = render_template(system_template_name)
    user_message = render_template(user_template_name)
    logger.info(system_message)
    logger.info(user_message)
    answer = send_request_to_llama_server(system_message, user_message)
    return answer

def correct_answer(answer, schema, plot, labels):
    system_template_name = "system.txt"
    user_template_name = "user-re.txt"
    system_message = render_template(system_template_name)
    user_message = render_template(user_template_name, answer=answer, plot=plot, labels=labels)
    schema_new = schema.copy()
    schema_new['properties']['corrections'] = {"type": "object", 
                                                    "properties": {
                                                        "old_class": {"type": "string"},
                                                        "new_class": {"type": "string"}
                                                        },
                                                    "required": ["old_class", "new_class"]
                                                    }
    schema_new['required'].append('corrections')
    
    resp = send_request_to_llama_server(system_message, user_message, json_mode=True, schema=schema_new)
    return resp


def loop(file_name, level, test=True, n_steps=1):
    
    data_root = TEST_ROOT if test else TRAIN_ROOT
    file_path = os.path.join(data_root, f'{file_name}.json')

    with open(f'zeroshot/data/zeroshot_topics_{level}.json', "r") as f:
        labels = list(json.load(f).values())

    schema = {
        "type": "object",
        "properties": {
            "chain of thoughts": {"type": "string"},
            "class": {"enum": labels}
        },
        "required": ["chain of thoughts", "class"]
    }

    system_prompt = render_template("system.txt")

    # Открываем файл для дозаписи
    out_file_path = os.path.join(data_root, f"pred_{file_name}.jsonl")

    with open(file_path, "r") as f:
        articles = json.load(f)

        for idx, article in enumerate(articles):
            user_prompt = render_template("user.txt", plot=article, labels=labels)

            # Получаем предсказание
            resp = send_request_to_llama_server(system_prompt, user_prompt, json_mode=True, schema=schema)
            pred_label = resp.get('class', None)

            logger.info(f"ID: {article.get('ID')}, Predicted label: {pred_label}")

            # Формируем словарь с ID и предсказанным лейблом
            result = {
                "ID": int(article.get('ID', -1)),  # преобразуем в int
                "pred_label": pred_label if pred_label is not None else ""
            }

            # Дозаписываем в файл
            with open(out_file_path, "a") as out_file:
                out_file.write(json.dumps(result) + "\n")

            # Очистка памяти
            del resp, user_prompt, result
            gc.collect()


if __name__ == "__main__":
    loop('test', level=1, test=True, n_steps=1)