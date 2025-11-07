# модуль для парсинга дополнительного блока информации при его наличии
import re

def extract_article_data(soup):
    # Ищем блок, который содержит текст "ОПИСАНИЕ НА АНГЛИЙСКОМ ЯЗЫКЕ"
    description_block = soup.find('font', string='ОПИСАНИЕ НА АНГЛИЙСКОМ ЯЗЫКЕ:')
    
    if not description_block:
        return None  # Если блок не найден, возвращаем None
    
    # родительский блок
    parent_td = description_block.find_parent('tbody')

    title = extract_title_en(parent_td)
    abstract = extract_abstract_en(parent_td)
    keywords = extract_keywords_en(parent_td)
    authors_metadata = extract_authors_metadata_en(parent_td)
    
    return title, keywords, abstract, authors_metadata

def extract_title_en(parent_td):
    ''' Ищем название статьи в родительском блоке '''
    title = parent_td.find('font', color="#F26C4F")  # Ищем название статьи 
    return title.get_text(strip=True) if title else None

def extract_keywords_en(parent_td): 
    ''' Ищем ключевые слова в родительском блоке '''
    keyword_tags = parent_td.find_all('a', href=re.compile(r'keyword_items\.asp\?id=\d+'))
    if keyword_tags:
        keywords_list = [tag.get_text(strip=True) for tag in keyword_tags]
        return keywords_list
    return None

def extract_abstract_en(parent_td):
    ''' Ищем аннотацию в родительском блоке '''
    abstract = parent_td.find('div', {'id': 'eabstract2'})
    if not abstract:
        abstract = parent_td.find('div', {'id': 'eabstract1'})
    return abstract.get_text(strip=True) if abstract else None

def extract_authors_metadata_en(soup):
    ''' Ищем авторов и учреждения в родительском блоке '''
    td = soup.find('td', {'width': '504'})
    divs = td.find_all('div', recursive=False)

    authors = []
    institutions = {}

    # авторы
    for div in divs:
        if 'white-space: nowrap' in (div.get('style') or ''):
            # ФИО обычно в font с цветом #00008f, но может быть и просто в font
            font_tag = div.find('font', color="#00008f") or div.find('font')
            sup_tag = div.find('sup')

            if font_tag:
                name = font_tag.get_text(strip=True).replace('\xa0', ' ')
                number = sup_tag.get_text(strip=True) if sup_tag else None
                authors.append({'Author': name, 'InstitutionNumber': number})

    # институты
    font_tags = td.find_all('font', color="#000000")
    for font_tag in font_tags:
        sup_tag = font_tag.find('sup')
        if sup_tag:
            number = sup_tag.get_text(strip=True)

            # Следующий тег — span или font с названием учреждения
            next_tag = font_tag.find_next_sibling()
            while next_tag and next_tag.name not in ['span', 'font']:
                next_tag = next_tag.find_next_sibling()

            if next_tag:
                inst_font = next_tag.find('font') if next_tag.name == 'span' else next_tag
                if inst_font:
                    institution = inst_font.get_text(strip=True)
                    institutions[number] = institution

    # финальный список формируется по соотвествию номеров сносок
    result = []
    for author in authors:
        inst_num = author.get('InstitutionNumber')
        inst = institutions.get(inst_num) if inst_num else None
        result.append({'Author': author['Author'], 'Institution': inst})

    return result if result else None
