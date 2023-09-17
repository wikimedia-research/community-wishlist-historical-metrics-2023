def process_wishes(page):
    sections = parse_sections(page)['parse']['sections']
    wishes = {}

    for sec in sections:
        if sec['line'].lower() in ['notes']:
            pass
        else:
            if int(sec['level']) == 2:
                sec_index = int(sec['index'])
                sec_number = int(sec['number'])

                votes_section = next((
                    v for v in sections
                    if v.get('line') == 'Votes' and sec_number < float(v.get('number')) < sec_number + 1
                ), None)

                wishes[sec_index] = {
                    'title': sec['line'],
                    'votes_sec_number': float(votes_section['number']),
                    'votes_index': int(votes_section['index'])
                }

    return wishes

def process_wishes_2016(page):
    sections = parse_sections(page)['parse']['sections']
    wishes = {}

    for sec in sections:
        if sec['line'].lower() in ['notes']:
            pass
        else:
            if int(sec['level']) == 2:
                sec_index = int(sec['index'])
                sec_number = int(sec['number'])

                discussion_section = next((
                    d for d in sections
                    if 'discussion' in d.get('line').lower() and sec_number < float(d.get('number')) < sec_number + 1
                ), None)

                votes_section = next((
                    v for v in sections
                    if 'voting' in v.get('line').lower() and sec_number < float(v.get('number')) < sec_number + 1
                ), None)

                wishes[sec_index] = {
                    'title': sec['line'],
                    'discussion_sec_number': float(discussion_section['number']),
                    'discussion_index': int(discussion_section['index']),
                    'votes_sec_number': float(votes_section['number']),
                    'votes_index': int(votes_section['index'])
                }

    return wishes




