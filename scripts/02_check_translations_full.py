"""
Check survey translations for consistency (same number of fields as English
version).

FULL VERSION

"""

import markdown
import json_tricks
import pandas as pd
import numpy as np
import pathlib


LANGUAGES = ('en', 'de', 'nl', 'it')
infile = pathlib.Path(__file__).parent.parent / 'data' / 'Question Layout.xlsx'
countries_path = pathlib.Path(__file__).parent.parent / 'data' / 'countries.json'
countries = json_tricks.load(str(countries_path))


def read_data(infile):
    excel_data = pd.read_excel(infile)
    excel_data = excel_data.loc[(~excel_data['page'].isnull()) &
                                (~excel_data['type'].isnull()), :]

    excel_data['session'] = excel_data['session'].astype(str)
    excel_data['page'] = excel_data['page'].astype('int')
    excel_data['choices_en'] = excel_data['choices_en'].astype(str)
    excel_data['title_en'] = excel_data['title_en'].astype('string')
    excel_data['type'] = excel_data['type'].astype('string')
    excel_data['onlyVisibleIf'] = excel_data['onlyVisibleIf'].astype('string')

    # Fill empty IDs
    idx = excel_data['id'].isnull()
    vals = [str(x) for x in range(1000, 1000+sum(idx))]
    excel_data.loc[idx, 'id'] = vals

    cols = ['session', 'page', 'id', 'type', 'required', 'endSurveyIfResponse',
            'onlyVisibleIf']
    cols.extend([f'title_{lang}' for lang in LANGUAGES])
    cols.extend([f'choices_{lang}' for lang in LANGUAGES])
    excel_data = excel_data[cols]

    return excel_data


def filter_data_by_session(data, session):
    data = data.copy()
    if session == 1:
        sessions = ('1', 'all')
        # first_page_is_welcome = True
    elif session == 'last':
        sessions = ('>1', 'all', 'last')
    elif session > 1:
        sessions = ('>1', 'all')
        # first_page_is_welcome = False

    data = data.loc[data['session'].isin(sessions), :]

    duplicated_ids = data['id'].duplicated()
    if duplicated_ids.any():
        msg = (f'The following questions had duplicated IDs: '
               f'{data[duplicated_ids]}')
        raise ValueError(msg)

    return data


def extract_question_data(q_data):
    q_type = q_data['type'].iloc[0]
    q_required = bool(q_data['required'].iloc[0])

    if q_data['onlyVisibleIf'].isnull().iloc[0]:
        q_visible_if = None
    else:
        q_visible_if = f"{q_data['onlyVisibleIf'].iloc[0]}"

    q_title = {lang: q_data[f'title_{lang}'].iloc[0]
               for lang in LANGUAGES}

    # Extract semi-colon-separated choices, and strip leading and
    # trailing whitespaces.
    if q_type in ['header', 'info', 'comment',
                  'country_selector', 'date', 'image', 'email']:
        q_choices = []
    else:
        choices = {}
        for lang in LANGUAGES:
            choices[lang] = q_data[f'choices_{lang}'].iloc[0]
            choices[lang] = choices[lang].split(';')
            choices[lang] = [c.strip() for c in choices[lang]]

        num_choices_en = len(choices['en'])
        for lang in LANGUAGES[1:]:
            if num_choices_en != len(choices[lang]):
                msg = (f'Mismatch in number of choices for en vs {lang}: '
                       f'{q_data["id"].iloc[0]}')
                print(msg)
                # Inject English choices so we can proceed.
                choices[lang] = choices['en']

        q_choices = []
        for idx, value in enumerate(choices['en']):
            text = {lang: choices[lang][idx]
                    for lang in LANGUAGES}
            q_choices.append({'value': value,
                              'text': text})

    return q_type, q_title, q_choices, q_required, q_visible_if


def gen_radio(q_id, q_title, q_choices, q_required=True, q_visible_if=''):
    question = {
        "type": "radiogroup",
        "name": q_id,
        "title": q_title,
        "choices": q_choices,
        "visibleIf": q_visible_if,
        "isRequired": q_required
    }

    return question


def gen_radio_with_other_option(q_id, q_title, q_choices, other_text,
                                q_required=True, q_visible_if=''):
    question = gen_radio(q_id=q_id, q_title=q_title, q_choices=q_choices,
                         q_required=q_required, q_visible_if=q_visible_if)
    question["hasOther"] = True
    question["otherText"] = other_text

    return question


def gen_checkbox(q_id, q_title, q_choices, q_required=True, q_visible_if=''):
    question = {
        "type": "checkbox",
        "name": q_id,
        "title": q_title,
        "choices": q_choices,
        "visibleIf": q_visible_if,
        "isRequired": q_required
    }

    return question


def gen_checkbox_with_other_option(q_id, q_title, q_choices, other_text,
                                   q_required=True, q_visible_if=''):
    question = gen_checkbox(q_id=q_id, q_title=q_title, q_choices=q_choices,
                            q_required=q_required, q_visible_if=q_visible_if)
    question["hasOther"] = True
    question["otherText"] = other_text

    return question


def gen_checkbox_with_none_option(q_id, q_title, q_choices, none_text,
                                  q_required=True, q_visible_if=''):

    if q_id == "taste_qual_6m":
        none_text = q_choices[-1]
        del q_choices[-1]

    question = gen_checkbox(q_id=q_id, q_title=q_title, q_choices=q_choices,
                            q_required=q_required, q_visible_if=q_visible_if)
    question["hasNone"] = True
    question["noneText"] = none_text

    return question


def gen_checkbox_with_other_and_none_options(q_id, q_title, q_choices,
                                             other_text, none_text,
                                             q_required=True, q_visible_if=''):
    question = gen_checkbox(q_id=q_id, q_title=q_title, q_choices=q_choices,
                            q_required=q_required, q_visible_if=q_visible_if)
    question["hasOther"] = True
    question["otherText"] = other_text
    question["hasNone"] = True
    question["noneText"] = none_text
    return question


def gen_slider(q_id, q_title, q_choices, q_required=True, q_visible_if=''):
    q_desc = dict()

    for lang in LANGUAGES:
        if '######' in q_title[lang]:
            title, desc = q_title[lang].split('######')
            q_title[lang] = title.strip()
            q_desc[lang] = desc.strip()
        else:
            q_desc[lang] = ""

    question = {
        "type": "nouislider",
        "name": q_id,
        "title": q_title,
        "description": q_desc,
        "rangeMin": 0,
        "rangeMax": 100,
        "pipsMode": "values",
        "pipsValues": [0, 100],
        "pipsDensity": 101,
        "pipsText": [dict(value=0, text=q_choices[0]['text']),
                     dict(value=100, text=q_choices[1]['text'])],
        "tooltips": False,
        "visibleIf": q_visible_if,
        "isRequired": q_required
    }

    return question


def gen_dropdown(q_id, q_title, q_choices, q_required=True, q_visible_if='',
                 previous_home_test_item=None):
    question = {
        "type": "dropdown",
        "name": q_id,
        "title": q_title,
        "choices": q_choices,
        "visibleIf": q_visible_if,
        "isRequired": q_required
    }

    if previous_home_test_item is not None:
        item = previous_home_test_item[q_id]
        question["defaultValue"] = item
        question["description"] = ("We have pre-selected the item you used "
                                   "last time, if any.")

    return question


def gen_comment(q_id, q_title, q_required=True, q_visible_if=''):
    question = {
        "type": "comment",
        "name": q_id,
        "title": q_title,
        "visibleIf": q_visible_if,
        "isRequired": q_required
    }

    return question


def gen_text(q_id, q_title, placeholder='', q_required=True, q_visible_if=''):
    question = {
        "type": "text",
        "name": q_id,
        "title": q_title,
        "placeHolder": placeholder,
        "inputType": "text",
        "visibleIf": q_visible_if,
        "isRequired": q_required
    }

    return question


def gen_email(q_id, q_title, q_required=True, q_visible_if=''):
    question = {
        "type": "text",
        "name": q_id,
        "title": q_title,
        "inputType": "email",
        "placeHolder": "me@domain.com",
        "visibleIf": q_visible_if,
        "isRequired": q_required
    }

    return question


def gen_number(q_id, q_title, placeholder='', q_required=True,
               q_visible_if=''):
    question = {
        "type": "text",
        "name": q_id,
        "title": q_title,
        "placeHolder": placeholder,
        "inputType": "number",
        "visibleIf": q_visible_if,
        "isRequired": q_required
    }

    return question


def gen_date(q_id, q_title, q_required=True, q_visible_if='', language='en'):
    question = {
        "type": "bootstrapdatepicker",
        "name": q_id,
        "title": q_title,
        "dateFormat": "yyyy-mm-dd",
        "visibleIf": q_visible_if,
        "isRequired": q_required,
        "startDate": "-6m",
        "endDate": "today",
        "todayHighlight": True,
        "clearBtn": True,
        "autoClose": True,
        "daysOfWeekHighlighted": "0,6",
        "weekStart": 0,
        "disableTouchKeyboard": True,
        "language": language
    }
    return question


def gen_year_selector(q_id, q_title, q_choices, q_required=True,
                      q_visible_if=''):
    choices = list(range(int(q_choices[0]['value']),
                         int(q_choices[1]['value'])+1))
    choices = choices[::-1]

    question = {
        "type": "dropdown",
        "name": q_id,
        "title": q_title,
        "choices": choices,
        "visibleIf": q_visible_if,
        "isRequired": q_required
    }

    return question


def gen_country_selector(q_id, q_title, q_required=True, q_visible_if='',
                         language='en'):
    names = []
    regions = []
    translations = []
    for country in countries:
        if country['name'] == 'Republic of Kosovo':  # Part of Serbia
            continue

        names.append(country['name'])
        if language == 'en':
            translations.append(country['name'])
        else:
            translations.append(country['translations'][language])

        regions.append(country['region'])

    df = pd.DataFrame(dict(name=names, translation=translations,
                           region=regions))
    df = df.sort_values(by='translation')

    q_choices = []
    for idx, value in enumerate(df['name']):
        text = {language: df['translation'].iloc[idx]}
        visible_if = "{region} = " + "'" + df['region'].iloc[idx] + "'"
        q_choices.append({'value': value,
                          'text': text,
                          'visibleIf': visible_if})

    question = {
        "type": "dropdown",
        "name": q_id,
        "title": q_title,
        "visibleIf": q_visible_if,
        "isRequired": q_required,
        "choices": q_choices
    }

    return question


def gen_header(q_id, q_title, q_visible_if=''):
    header = {
        "type": "html",
        "name": q_id,
        "html":  f"<h1>{q_title}</h1>",
        "visibleIf": q_visible_if
    }

    return header


def gen_info(q_id, q_title, q_visible_if=''):
    html = dict()
    for lang, text in q_title.items():
        html[lang] = markdown.markdown(text)

    info = {
        "type": "html",
        "name": q_id,
        "html": html,
        "visibleIf": q_visible_if
    }

    return info


def gen_image(q_id, filename, q_visible_if=''):
    question = {
        "type": "image",
        "name": q_id,
        "imageLink": f'assets/{filename}',
        "visibleIf": q_visible_if
    }

    return question


def gen_question(*, q_id, q_data, previous_home_test_item, language,
                 other_text, none_text):
    extracted = extract_question_data(q_data)
    q_type, q_title, q_choices, q_required, visible_if = extracted

    if q_type == 'radio':
        question = gen_radio(q_id=q_id, q_title=q_title, q_choices=q_choices,
                             q_required=q_required, q_visible_if=visible_if)
    elif q_type == 'radio_with_other_option':
        question = gen_radio_with_other_option(q_id=q_id, q_title=q_title,
                                               q_choices=q_choices,
                                               q_required=q_required,
                                               q_visible_if=visible_if,
                                               other_text=other_text)
    elif q_type == 'checkbox':
        question = gen_checkbox(
            q_id=q_id, q_title=q_title,
            q_choices=q_choices, q_required=q_required,
            q_visible_if=visible_if)
    elif q_type == 'checkbox_with_other_option':
        question = gen_checkbox_with_other_option(q_id=q_id, q_title=q_title,
                                                  q_choices=q_choices,
                                                  q_required=q_required,
                                                  q_visible_if=visible_if,
                                                  other_text=other_text)
    elif q_type == 'checkbox_with_none_option':
        question = gen_checkbox_with_none_option(
            q_id=q_id,
            q_title=q_title,
            q_choices=q_choices,
            q_required=q_required,
            q_visible_if=visible_if,
            none_text=none_text)
    elif q_type == 'checkbox_with_other_and_none_options':
        question = gen_checkbox_with_other_and_none_options(
            q_id=q_id,
            q_title=q_title,
            q_choices=q_choices,
            q_required=q_required,
            q_visible_if=visible_if,
            other_text=other_text,
            none_text=none_text)
    elif q_type == 'slider':
        question = gen_slider(q_id=q_id, q_title=q_title, q_choices=q_choices,
                              q_required=q_required, q_visible_if=visible_if)
    elif q_type == 'comment':
        question = gen_comment(q_id=q_id, q_title=q_title,
                               q_required=q_required, q_visible_if=visible_if)
    elif q_type == 'text':
        question = gen_text(q_id=q_id, q_title=q_title,
                            placeholder=q_choices[0],
                            q_required=q_required, q_visible_if=visible_if)
    elif q_type == 'email':
        question = gen_email(q_id=q_id, q_title=q_title,
                             q_required=q_required, q_visible_if=visible_if)
    elif q_type == 'number':
        question = gen_number(q_id=q_id, q_title=q_title,
                              placeholder=q_choices[0],
                              q_required=q_required, q_visible_if=visible_if)
    elif q_type == 'dropdown':
        question = gen_dropdown(
            q_id=q_id, q_title=q_title,
            q_choices=q_choices, q_required=q_required,
            q_visible_if=visible_if,
            previous_home_test_item=previous_home_test_item)
    elif q_type == 'year_selector':
        question = gen_year_selector(q_id=q_id, q_title=q_title,
                                     q_choices=q_choices,
                                     q_required=q_required,
                                     q_visible_if=visible_if)
    elif q_type == 'country_selector':
        question = gen_country_selector(q_id=q_id, q_title=q_title,
                                        q_required=q_required,
                                        q_visible_if=visible_if,
                                        language=language)
    elif q_type == 'info':
        question = gen_info(q_id=q_id, q_title=q_title,
                            q_visible_if=visible_if)
    elif q_type == 'header':
        question = gen_header(q_id=q_id, q_title=q_title,
                              q_visible_if=visible_if)
    elif q_type == 'image':
        question = gen_image(q_id=q_id, filename=q_title,
                             q_visible_if=visible_if)
    elif q_type == 'study_id':
        question = gen_text(q_id=q_id, q_title=q_title,
                            placeholder=q_choices[0],
                            q_required=q_required, q_visible_if=visible_if)
    elif q_type == 'date':
        question = gen_date(q_id=q_id, q_title=q_title,
                            q_required=q_required, q_visible_if=visible_if,
                            language=language)
    else:
        raise ValueError(f'Unknown question type: {q_type}')

    return question


def gen_pages(data, previous_home_test_item, language):
    pages = []

    NONE_TEXT = {lang: (data
                        .loc[data['id'] == 'msg_none', f'title_{lang}']
                        .iloc[0])
                 for lang in LANGUAGES}

    OTHER_TEXT = {lang: (data
                         .loc[data['id'] == 'msg_other', f'title_{lang}']
                         .iloc[0])
                  for lang in LANGUAGES}

    for page_id, page_data in data.groupby('page', sort=False):
        page = dict(name=str(page_id), elements=[])
        pages.append(page)

        for question_id, question_data in page_data.groupby('id', sort=False):
            element = gen_question(
                q_id=question_id, q_data=question_data,
                previous_home_test_item=previous_home_test_item,
                language=language, other_text=OTHER_TEXT, none_text=NONE_TEXT)
            page['elements'].append(element)

    return pages


def gen_triggers(data):
    questions_with_triggers = (data
                               .loc[~data['endSurveyIfResponse']
                                    .isnull(), :])

    triggers = []
    for question_id, question_data in (questions_with_triggers
                                       .groupby('id', sort=False)):
        trigger_if = question_data['endSurveyIfResponse'].iloc[0]

        if trigger_if.startswith('>='):
            comparison = '>='
            trigger_if = trigger_if.split('>=')[1].strip()
        else:
            comparison = '='

        trigger = dict(
            type="complete",
            expression=f"{{{question_id}}} {comparison} '{trigger_if}'")
        triggers.append(trigger)

    return triggers


def randomize_taste_order(data):
    data = data.copy()

    tastes = ('sweet', 'sour', 'salty', 'bitter')
    taste_vals = dict()
    taste_idx = dict()
    taste_page = dict()
    for taste in tastes:
        taste_vals[taste] = (data
                             .loc[[taste in i for i in data['id']], :]
                             .copy())
        taste_idx[taste] = taste_vals[taste].index
        taste_page[taste] = taste_vals[taste]['page'].values[0]

    random_taste_order = np.random.choice(tastes, 4, replace=False)
    first_taste_page = sorted(taste_page.values())[0]
    randomized_taste_vals = list()

    page = first_taste_page
    for taste in random_taste_order:
        vals = taste_vals[taste]
        vals['page'] = [page] * 3
        randomized_taste_vals.append(vals)
        page += 1

    first_taste_idx = np.array(list(taste_idx.values())).flatten().min()
    randomized_taste_idx = list()

    taste_idx = first_taste_idx
    for _ in tastes:
        for i in range(3):
            randomized_taste_idx.append(taste_idx + i)
        taste_idx += 3

    randomized_taste_df = pd.DataFrame()
    for vals in randomized_taste_vals:
        randomized_taste_df = randomized_taste_df.append(vals,
                                                         ignore_index=True)

    randomized_taste_df.index = randomized_taste_idx

    # Add "how to taste" graphics.
    for lang in LANGUAGES:
        col = f'title_{lang}'
        how_to_taste = data.loc[data['id'] == 'how_to_taste', col].iloc[0]
        idx = randomized_taste_df.index[1]
        randomized_taste_df.loc[idx, col] += f'\n\n{how_to_taste}'

    data.loc[randomized_taste_idx, :] = randomized_taste_df
    return data


def gen_survey_json(infile, session, previous_home_test_item, language):
    data = read_data(infile)
    data = filter_data_by_session(data=data, session=session)
    data = randomize_taste_order(data)

    pages = gen_pages(data=data,
                      previous_home_test_item=previous_home_test_item,
                      language=language)
    triggers = gen_triggers(data=data)

    first_page_is_welcome = False

    json = {
        "triggers": triggers,
        "pages": pages,
        "questionTitlePattern": "numRequireTitle",
        "requiredText": "*",
        "showQuestionNumbers": "none",
        "showProgressBar": "top",
        "firstPageIsStarted": first_page_is_welcome,
        "startSurveyText": "Start Survey",
        "focusFirstQuestionAutomatic": False,
        "showCompletedPage": False,
        "storeOthersAsComment": True,
        "maxTextLength": 10000,
        "maxOthersLength": 10000
    }

    json = json_tricks.dumps(json, sort_keys=False)
    return json


def gen_html_elements(infile, language):
    data = read_data(infile)
    data = data.loc[[True if x.startswith('msg') else False
                     for x in data['id']], :]

    title_row = f'title_{language}'
    html_item = dict()
    for _, row in data.iterrows():
        name = row['id']
        content_markdown = row[title_row]
        content_html = markdown.markdown(content_markdown)
        if (name.startswith('msg_button') or
                name == 'msg_title' or
                name.startswith('msg_chart') or
                name == 'msg_no_completed_checks'):
            content_html = (content_html
                            .strip('<p>')
                            .strip('</p>')
                            .replace('&amp;', '&'))
        html_item[name] = content_html

    json = json_tricks.dumps(html_item, sort_keys=False)
    return json


if __name__ == '__main__':
    sessions = [1, 2]

    for language, session in zip(LANGUAGES, sessions):
        gen_survey_json(infile=infile, session=session, language=language,
                        previous_home_test_item=None)
