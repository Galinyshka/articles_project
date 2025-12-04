from get_response import send_request_to_llama_server
import json 
import gc
import os 
from formatter import render_template
from logger import logger

TEST_ROOT = 'zeroshot/data/test/'
TRAIN_ROOT = 'zeroshot/data/train/'

'''def request_validation():
    system_message = render_template("system.txt")
    user_message = render_template("user.txt")
    logger.info(system_message)
    logger.info(user_message)
    answer = send_request_to_llama_server(system_message, user_message)
    return answer'''

def correct_answer(answer, schema, plot, labels):
    system_message = render_template("system.txt")
    user_message = render_template("user-re.txt", answer=answer, plot=plot, labels=labels)
    #schema_new = schema.copy()
    #schema_new['properties']['corrections'] = {"type": "object", 
    #                                                "properties": {
    #                                                    "old_class": {"type": "string"},
    #                                                    "new_class": {"type": "string"}
    #                                                    },
    #                                                "required": ["old_class", "new_class"]
    #                                                }
    #schema_new['required'].append('corrections')
    
    resp = send_request_to_llama_server(system_message, user_message, json_mode=True, schema=schema)
    return resp


def loop(file_name, level, test=True, n_steps=1):
    
    data_root = TEST_ROOT if test else TRAIN_ROOT
    file_path = os.path.join(data_root, f'{file_name}.json')

    with open(f'zeroshot/data/zeroshot_topics_{level}.json', "r") as f:
        if level == 1:
            labels = list(json.load(f).values())
        else:
            data = json.load(f) 
            labels = list(data[file_name[-1]].values())
            labels2 = []
            for i in range(6):
                if i != int(file_name[-1]):
                    labels2.extend(list(data[str(i)].values()))


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
    out_file_path = os.path.join(data_root, f"pred_5_{file_name}.jsonl")
    with open(file_path, "r") as f:
        articles = json.load(f)

        #start_processing = False  

        for idx, article in enumerate(articles):

            # Проверяем, достигли ли нужного ID
            #if article.get('ID') == 50390912:
            #    start_processing = True  # Устанавливаем флаг, чтобы начать обработку
            #if not start_processing:
            #    continue  # Пропускаем записи до нужного ID

            user_prompt = render_template("user.txt", plot=article, labels=labels)
            # Получаем предсказание
            resp = send_request_to_llama_server(system_prompt, user_prompt, json_mode=True, schema=schema)
            pred_label = resp.get('class', None)

            logger.info(f"ID: {article.get('ID')}, Predicted label: {pred_label}")

            # Список для хранения всех предсказанных классов с порядковыми номерами
            predicted_classes = []
            predicted_classes.append({"step": 1, "class": pred_label})
            

            for _ in range(2, n_steps):
                previous_classes = ", ".join([predicted_classes[i]['class'] for i in range(len(predicted_classes))])
                print(previous_classes)
                # Получаем исправленный ответ
                resp = correct_answer(answer=previous_classes, schema=schema, plot=article, labels=labels)
                logger.info(f"Corrected answer: {resp}")

                corrected_class = resp.get('class', None)
                last_class = predicted_classes[-1]['class']
                predicted_classes.append({"step": len(predicted_classes) + 1, "class": corrected_class})

                if corrected_class == last_class and corrected_class != 'None':
                    logger.info("No changes in class. Converged.")
                    break
                else:
                    logger.info("Class changed. Continuing to next step.")
            
            # Формируем результат с сохранением всех предсказанных классов
            result = {
                "ID": article.get('ID', -1),
                "predicted_classes": predicted_classes
            }
            
            # Логируем результат
            logger.info(f"Final result: {result}") 

            # Дозаписываем в файл
            with open(out_file_path, "a") as out_file:
                out_file.write(json.dumps(result) + "\n")

            # Очистка памяти
            del resp, user_prompt, result
            gc.collect()


if __name__ == "__main__":
    for i in range(6):
    #    loop(f'instruction_{i}', level=2, test=True, n_steps=6)
        loop(f'{i}', level=2, test=True, n_steps=6)

   # loop('test', level=1, test=True, n_steps=6)