import pandas as pd
import requests
import re
import wmfdata as wmf

cws_links = pd.read_csv('data/cws_page_links.tsv', sep='\t')
api_endpoint = 'https://api-ro.discovery.wmnet/w/api.php'
host_wiki = {'Host': 'meta.wikimedia.org'}

def get_title(year, page, replace_space=True, df=cws_links):
    title = df.query("year == @year")[page].values[0]
    
    if replace_space:
        return title.replace(' ', '_')
    else:
        return title

def get_wikitext(page_title, url=api_endpoint, headers=host_wiki, section_index=None):
    
    params = {
        "action": "parse", 
        "format": "json", 
        "page": page_title, 
        "prop": "wikitext", 
    }
    
    if section_index == None:
        pass
    else:
        params['section'] = section_index
        
    return requests.get(url, headers=headers, params=params, verify=False).json()

def parse_page_sections(page, url=api_endpoint, headers=host_wiki):
    
    params = {
        'action': 'parse',
        'page': page,
        'prop': 'sections',
        'format': 'json'
    }
    
    return requests.get(url, headers=headers, params=params, verify=False).json()

def get_section_index(section, page_sections):
    return next((
        d for d in page_sections
        if section.strip() in d.get('line').lower().strip()
    ), None)['index']

def parse_iwlinks(page_title, url=api_endpoint, headers=host_wiki, section_index=None):
    
    params = {
        'action': 'parse',
        'page': page_title,
        'prop': 'links',
        'format': 'json'
    }
    
    if section_index == None:
        pass
    else:
        params['section'] = section_index
    
    return requests.get(url, headers=headers, params=params, verify=False).json()

def extract_phab_tickets(blob):
    pattern = r'\b(T\d+)\b'
    return re.findall(pattern, blob)

def extract_usernames_from_parser(api_response):
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
    pattern = r"'''Proposer''':.*?(?:(?:en:)?User(?:_?talk)?|User talk):(.*?)[\|\[]"
    
    match = re.search(pattern, text)
    if match:
        return match.group(1).strip()
    else:
        return None
    
def extract_usernames_from_text(blob):
    pattern = r'\[\[User:([^\]|]*)'
    matches = re.findall(pattern, blob)
    return list(set([match.strip() for match in matches]))

def split_sections_l2(wikitext):
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
    
def get_redirect_target(proposal):
    return re.findall(r'#REDIRECT \[\[(.*?)\]\]', get_wikitext(proposal)['parse']['wikitext']['*'])[0]

def get_ar_category(proposal, year):
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

def get_categories_std(category_subpages, survey_title, year):
    query = """
    SELECT
        REPLACE(page_title, '{SURVEY_TITLE}/', '') AS category,
        page_title AS category_title
    FROM
        categorylinks cl
        JOIN page p
        ON cl.cl_from = p.page_id
    WHERE
        cl_to = '{CATEGORY_TITLE}' 
        AND page_title LIKE '{SURVEY_TITLE}/%'
    ORDER BY
        category_title
    """
    
    categories = wmf.mariadb.run(query.format(CATEGORY_TITLE=category_subpages, 
                                              SURVEY_TITLE=survey_title), dbs='metawiki')
    
    archive_category = pd.DataFrame({
        'category': 'Archive',
        'category_title': get_title(year, 'archive_page')
    }, 
        index=pd.Index([0])
    )    
    
    return pd.concat([categories, archive_category], ignore_index=True)

def process_wishes_201516(page, year):
    sections = parse_page_sections(page)['parse']['sections']
    wishes = {}

    for sec in sections:
        if sec['line'].lower() not in ['notes'] and int(sec['level']) == 2:
            sec_index = int(sec['index'])
            sec_number = int(sec['number'])

            wish_data = {
                'title': sec['line']
            }

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

def split_proposal_2015(wish_text):
    splits = re.split('{{collapse top', wish_text)
    discussion_splits = re.split('collapse bottom}}', splits[1])
    return splits[0], discussion_splits[0]

def convert_errors_to_strings(dictionary):

    for year, data in dictionary.items():
        if isinstance(data, dict):

            for key, value in data.items():
                if isinstance(value, dict) and 'error' in value:

                    value['error'] = str(value['error'])
                elif isinstance(value, str):
                    data[key] = str(value)
    return dictionary