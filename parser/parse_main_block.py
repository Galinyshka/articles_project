# модуль для парсинга основного блока с информацией о статье
import re
from bs4 import BeautifulSoup, NavigableString

def extract_article_title(soup):
    article_title = None
    # по тегу <p> с классом "bigtext" ищем заголовок
    title_tag = soup.find('p', class_='bigtext')

    #извлекаем текст
    if title_tag:
        article_title = title_tag.get_text()
    
    return article_title


def extract_keywords(soup):
    ''' Ищем ключевые слова'''
    # находим тег, который содержит текст "КЛЮЧЕВЫЕ СЛОВА:".
    # далее переходим к родительскому тегу <td>, который содержит сами ключевые слова.
    keyword_label_font = soup.find('font', string='КЛЮЧЕВЫЕ СЛОВА:')

    keywords_list = []

    if keyword_label_font:
        # Нашли тег <font> с меткой. Теперь найдем его родительский тег <td>.
        keyword_label_td = keyword_label_font.find_parent('td')

        if keyword_label_td:
            # Нашли <td> с меткой. Теперь найдем его родительский тег <tr>.
            label_tr = keyword_label_td.find_parent('tr')

            if label_tr:
                # Нашли строку с меткой. Теперь найдем следующую строку (где находятся ключевые слова).
                keywords_tr = label_tr.find_next_sibling('tr')

                if keywords_tr:
                    # Нашли строку с ключевыми словами. Теперь найдем второй <td> в этой строке.
                    all_tds_in_keywords_tr = keywords_tr.find_all('td')

                    if len(all_tds_in_keywords_tr) > 1:
                        keywords_td = all_tds_in_keywords_tr[1]

                        # Найдем все теги <a> внутри этого <td> (это и есть ключевые слова)
                        keyword_tags = keywords_td.find_all('a')

                        # Извлекаем текст из каждого тега <a> и добавляем в список
                        keywords_list = [tag.get_text().strip() for tag in keyword_tags]

    return keywords_list

def extract_abstract(soup):
    ''' Ищем аннотацию '''
    abstract_text = None
    # Find the div with id="abstract2" which contains the full abstract
    full_abstract_div = soup.find('div', id='abstract2')
    if not full_abstract_div:
        full_abstract_div = soup.find('div', id='abstract1')

    # Find the p tag within the full abstract div
    if full_abstract_div:
        abstract_p_tag = full_abstract_div.find('p')

        # Extract the text from the p tag
        if abstract_p_tag:
            abstract_text = abstract_p_tag.get_text().strip()

    return abstract_text

def extract_authors(soup):
    ''' Ищем авторов и институты '''
    authors = {}
    institutions = {}

    # td-блок, содержащий всю информацию об авторах и институтах
    td = soup.find('td', {'width': '514'})
    children = list(td.children)

    # разделяем по строке <div style="height:10px;"></div>
    split_index = None
    for i, tag in enumerate(children):
        if isinstance(tag, str):
            continue
        if tag.name == 'div' and tag.get('style') == 'height:10px;':
            split_index = i
            break

    # авторы
    for tag in children[:split_index]:
        if tag.name == 'div' and 'white-space: nowrap' in (tag.get('style') or ''):
            name_tag = tag.find('b')
            sup_tag = tag.find('sup')
            if name_tag and sup_tag:
                name = name_tag.get_text(strip=True).replace('\xa0', ' ')
                number = sup_tag.get_text(strip=True)
                authors[name] = number

    # институты
    for tag in children[split_index+1:]:
        if isinstance(tag, str) or tag.name != 'font':
            continue
        sup_tag = tag.find('sup')
        if not sup_tag:
            continue
        number = sup_tag.get_text(strip=True)
        

        next_tag = tag.find_next_sibling()
        while next_tag and not (next_tag.name in ['font', 'span']):
            next_tag = next_tag.find_next_sibling()
        
        # название института
        inst_font = next_tag.find('font') if next_tag and next_tag.name == 'span' else next_tag
        if inst_font:
            institution = inst_font.get_text(strip=True)
            institutions[number] = institution

    authors_metadata = []

    if authors and institutions:
        for author, number in authors.items():
            institution = []
            for i in range(0, len(number), 2):
                institution.append(institutions.get(number[i]))
            author_clean = author.strip() if author and author.strip() else None
            
            if institution:
                institution = ', '.join(institution)
            else:
                institution = None

            authors_metadata.append({
                'Author': author_clean,
                'Institution': institution
            })
    else:
        authors_metadata = None
    
    return authors_metadata

def extract_journal_info(soup):
    ''' Извлекает информацию о журнале: название журнала, издательство, ISSN и eISSN.'''
    journal_name = None
    publisher = None
    issn = None
    eissn = None

    # Ищем таблицу с нужной шириной, где содержится информация о журнале
    data_td = soup.find('td', width="504")
    if data_td:
        # Внутри ячейки ищем ссылку на журнал, чтобы получить его название
        journal_link = data_td.find('a', href=re.compile(r'contents\.asp\?id=\d+'))
        if journal_link:
            journal_name = journal_link.string.strip()

        # Вспомогательная функция: ищет значение после определённой текстовой метки
        def extract_data_after_label_sibling(element, label_text):
            # Находит строку с заданной меткой
            label_node = element.find(string=re.compile(rf'\s*{re.escape(label_text)}\s*'))
            if label_node:
                # Пробуем найти следующий тег <font>, который обычно содержит значение
                font_tag = label_node.find_next_sibling('font')
                if font_tag:
                    return font_tag.string.strip()

                # Если <font> нет, пробуем взять значение как следующий текстовый узел
                next_sib = label_node.next_sibling
                if isinstance(next_sib, NavigableString):
                    value = next_sib.strip().replace('\xa0', '').strip()
                    if value:
                        return value
            return None

        # Получаем весь текст с разметкой <br> заменённой на переносы строк
        text_content = data_td.decode_contents().replace('<br/>', '\n').replace('<br>', '\n')
        soup_text = BeautifulSoup(text_content, 'html.parser').get_text(separator=' ', strip=True)

        # Извлекаем издательство через регулярное выражение, оно обычно перед ISSN
        match = re.search(r'Издательство:\s*(.*?)\s*(?:ISSN:|eISSN:|$)', soup_text, re.IGNORECASE)
        if match:
            publisher = match.group(1).strip()

        # Ищем ISSN и eISSN по меткам
        issn = extract_data_after_label_sibling(data_td, "ISSN:")
        eissn = extract_data_after_label_sibling(data_td, "eISSN:")
    
    return journal_name, publisher, issn, eissn

def extract_article_info(soup):
    ''' Извлекает информацию о статье: тип статьи, язык публикации и год издания'''
    article_type = None
    language = None
    year = None

    # Ищем все теги <td> с заданной шириной — в них находится нужная информация
    td_elements = soup.find_all('td', width="574")

    # Вспомогательная функция: ищет значение после определённой текстовой метки
    def extract_data_after_label(element, label_text):
        label_node = element.find(string=re.compile(rf'\s*{re.escape(label_text)}\s*'))
        if label_node:
            font_tag = label_node.find_next_sibling('font')
            if font_tag:
                return font_tag.string.strip()
        return None

    # Перебираем все найденные ячейки таблицы
    for td in td_elements:
        # Ищем тип статьи
        current_type = extract_data_after_label(td, "Тип:")
        if current_type:
            article_type = current_type

        # Ищем язык статьи
        current_lang = extract_data_after_label(td, "Язык:")
        if current_lang:
            language = current_lang
            
        # Ищем год публикации (может встречаться в разных местах)
        current_year = extract_data_after_label(td, "Год:")
        if current_year:
            year = current_year
    
    return article_type, language, year


def extract_rubric(soup):
    """Извлекает рубрику OECD"""
    rubric_span = soup.find('span', id='rubric_oecd')
    if rubric_span:
        return rubric_span.get_text(strip=True)
    return None