def process_wishes(page, year=2015):
    sections = parse_sections(page)['parse']['sections']
    wishes = {}

    for sec in sections:
        if sec['line'].lower() in ['notes']:
            continue
        
        if int(sec['level']) == 2:
            sec_index = int(sec['index'])
            sec_number = int(sec['number'])

            wish_data = {'title': sec['line']}
            
            if year == 2015:
                votes_section = next((
                    v for v in sections
                    if v.get('line') == 'Votes' and sec_number < float(v.get('number')) < sec_number + 1
                ), None)

                if votes_section:
                    wish_data.update({
                        'votes_sec_number': float(votes_section['number']),
                        'votes_index': int(votes_section['index'])
                    })
            
            elif year == 2016:
                discussion_section = next((
                    d for d in sections
                    if 'discussion' in d.get('line').lower() and sec_number < float(d.get('number')) < sec_number + 1
                ), None)

                votes_section = next((
                    v for v in sections
                    if 'voting' in v.get('line').lower() and sec_number < float(v.get('number')) < sec_number + 1
                ), None)

                if discussion_section:
                    wish_data.update({
                        'discussion_sec_number': float(discussion_section['number']),
                        'discussion_index': int(discussion_section['index'])
                    })

                if votes_section:
                    wish_data.update({
                        'votes_sec_number': float(votes_section['number']),
                        'votes_index': int(votes_section['index'])
                    })

            wishes[sec_index] = wish_data

    return wishes

def get_title(year, page, replace_space=True, df=cws_links):
    title = df.query("year == @year")[page].values[0]
    
    if replace_space:
        return title.replace(' ', '_')
    else:
        return title
    
def parse_page_sections(page, url=api_endpoint, headers=host_wiki):
    
    params = {
        'action': 'parse',
        'page': page,
        'prop': 'sections',
        'format': 'json'
    }
    
    return requests.get(url, headers=headers, params=params, verify=False).json()

def get_wikitext(page_title, url=api_endpoint, headers=host_wiki, section=None):
    
    params = {
        "action": "parse", 
        "format": "json", 
        "page": page_title, 
        "prop": "wikitext", 
    }
    
    if section == None:
        pass
    else:
        params['section'] = section
        
    return requests.get(url, headers=headers, params=params, verify=False).json()

def parse_iwlinks(page_title, url=api_endpoint, headers=host_wiki, section_index=None):
    
    params = {
        'action': 'parse',
        'page': page_title,
        'prop': 'links',
        'format': 'json'
    }
    
    if section == None:
        pass
    else:
        params['section'] = section_index
    
    return requests.get(url, headers=headers, params=params, verify=False).json()

def extract_phab_tickets(blob):
    pattern = r'\b(T\d+)\b'
    return re.findall(pattern, blob)

def extract_usernames_via_parser(api_response):
    userlinks = api_response['parse']['links']
    usernames = set() 
    
    for link in userlinks:
        if link['*'].startswith('User:'):
            usernames.add(link['*'][5:])
        elif link['*'].startswith('User talk:'):
            usernames.add(link['*'][10:])
    
    return list(usernames)

def extract_proposals(text):
    pattern = r'{{:([^}]+)}}'
    matches = re.findall(pattern, text)
    return [m for m in matches if 'Category header' not in m]

def extract_proposer_username(text):
    pattern = r"'''Proposer''': \[\[User:(.*?)\|"
    match = re.search(pattern, text)
    if match:
        return match.group(1)
    else:
        return None
    
def split_sections(wikitext):
    sections = re.split(r'==[^=]+==', wikitext)[1:]
    return sections

def extract_reject_reason(text):
    pattern = r'<!-- DO NOT EDIT ABOVE THIS LINE -->(.*?)\* \'\'\'Problem\'\'\''
    
    match = re.search(pattern, text, re.DOTALL)
    
    if match:
        reject_reason = match.group(1)
        
        reject_reason = re.sub(r'\[\[File:.*\]\]', '', reject_reason)
        reject_reason = re.sub(r'\{\{[^}]+\}\}', '', reject_reason)

        
        
        return reject_reason.strip().strip(" '")
    else:
        return None
    
    
def get_section_index(section, page_sections):
    return next((
        d for d in page_sections
        if section in d.get('line').lower()
    ), None)['index']

def get_redirect_target(proposal):
    return re.findall(r'#REDIRECT \[\[(.*?)\]\]', get_wikitext(proposal)['parse']['wikitext']['*'])[0]

def get_ar_category(proposal):
    plinks_query = """
        SELECT 
            page_title
        FROM 
            pagelinks pl
            JOIN page p 
            ON pl.pl_from = p.page_id
        WHERE 
            pl_title = '{PAGE_TITLE}'
            AND page_is_redirect
            AND page_title NOT LIKE '%Archive%'
            AND page_title LIKE '{SURVEY_TITLE}/%'
    """
    
    old_title =  wmf.mariadb.run(plinks_query.format(PAGE_TITLE=proposal.replace(' ', '_'), SURVEY_TITLE=get_title(year, 'main_page').replace(' ', '_')), dbs='metawiki')
    return old_title['page_title'].values[0]

def extract_usernames_from_text(blob):
    pattern = r'\[\[User:([^\]|]*)'
    matches = re.findall(pattern, blob)
    return list(set([match.strip() for match in matches]))

def split_sections_from text(wikitext):
    sections = re.split(r'==[^=]+==', wikitext)[1:]
    return sections

#2015 only
def split_proposal_2015(wish_text):
    splits = re.split('{{collapse top', wish_text)
    discussion_splits = re.split('collapse bottom}}', splits[1])
    return splits[0], discussion_splits[0]

#2016
def get_dparticipants_api(category_title, wish_index, url=api_endpoint):
    vote_params = {
        'action': 'parse',
        'page': category_title,
        'section': wish_index['discussion_index'],
        'prop': 'links',
        'format': 'json'
    }
    return requests.get(url, headers=headers, params=vote_params, verify=False).json()