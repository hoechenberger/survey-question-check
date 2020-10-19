"""
Check survey translations for consistency (same number of fields as English
version).

REDUCED VERSION

"""

import json_tricks
import pandas as pd
import pathlib


LANGUAGES = ('en', 'de', 'nl', 'it', 'ru', 'ja')
infile = pathlib.Path(__file__).parent.parent / 'data' / 'Question Layout.xlsx'
countries_path = (pathlib.Path(__file__).parent.parent / 'data' /
                  'countries.json')
with open(countries_path, encoding='utf8') as f:
    countries = json_tricks.load(f)


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
        print(q_title)
        for lang in LANGUAGES:
            choices[lang] = q_data[f'choices_{lang}'].iloc[0]
            choices[lang] = choices[lang].split(';')
            choices[lang] = [c.strip() for c in choices[lang]]

        num_choices_en = len(choices['en'])
        for lang in LANGUAGES[1:]:
            if num_choices_en != len(choices[lang]):
                msg = (f'Mismatch in number of choices for en vs {lang}: '
                       f'{q_data["id"].iloc[0]}\n\n'
                       f'\ten:\n')

                for choice in choices["en"]:
                    msg += f'\t- {choice}\n'

                msg += f'\n\t{lang}:\n'
                for choice in choices[lang]:
                    msg += f'\t- {choice}\n'

                print(msg)

        q_choices = []

    return q_type, q_title, q_choices, q_required, q_visible_if


def gen_question(*, q_id, q_data, previous_home_test_item, language,
                 other_text, none_text):
    q_type, q_title, q_choices, q_required, q_visible_if = extract_question_data(q_data)

    if q_type not in ('radio', 'radio_with_other_option', 'checkbox',
                      'checkbox_with_other_option',
                      'checkbox_with_none_option',
                      'checkbox_with_other_and_none_options', 'slider',
                      'comment', 'text', 'email', 'number', 'dropdown',
                      'year_selector', 'country_selector', 'info', 'header',
                      'image', 'study_id', 'date'):
        raise ValueError(f'Unknown question type: {q_type}')


def gen_pages(data, previous_home_test_item, language):
    NONE_TEXT = {lang: (data
                        .loc[data['id'] == 'msg_none', f'title_{lang}']
                        .iloc[0])
                 for lang in LANGUAGES}

    OTHER_TEXT = {lang: (data
                         .loc[data['id'] == 'msg_other', f'title_{lang}']
                         .iloc[0])
                  for lang in LANGUAGES}

    for _, page_data in data.groupby('page', sort=False):
        for question_id, question_data in page_data.groupby('id', sort=False):
            gen_question(
                q_id=question_id, q_data=question_data,
                previous_home_test_item=previous_home_test_item,
                language=language, other_text=OTHER_TEXT, none_text=NONE_TEXT)


def gen_survey_json(infile, session, language):
    data = read_data(infile)
    data = filter_data_by_session(data=data, session=session)

    gen_pages(data=data,
              previous_home_test_item=None,
              language=language)


def gen_html_elements(infile, language):
    data = read_data(infile)
    data = data.loc[[True if x.startswith('msg') else False
                     for x in data['id']], :]

    title_row = f'title_{language}'
    for _, row in data.iterrows():
        name = row['id']
        content_markdown = row[title_row]


if __name__ == '__main__':
    sessions = [1, 2]

    for language, session in zip(LANGUAGES, sessions):
        gen_survey_json(infile=infile, session=session, language=language)
