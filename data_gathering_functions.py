import pandas as pd
import requests
import re
import wmfdata as wmf

# manually curated file with information related to varioys iterations of the survey
# such as links to category page, results page, category structure etc.
cws_links = pd.read_csv('data/cws_page_links.tsv', sep='\t')

api_endpoint = 'https://api-ro.discovery.wmnet/w/api.php'
host_wiki = {'Host': 'meta.wikimedia.org'}

def get_title(year, page, replace_space=True, df=cws_links):
    
    # get title of a page for a given year
    # page can be category page, results page, category subpages etc.
    
    title = df.query("year == @year")[page].values[0]
    
    if replace_space:
        return title.replace(' ', '_')
    else:
        return title

def get_wikitext(page_title, url=api_endpoint, headers=host_wiki, section_index=None):
    
    # get wikitext of a page
    # section index can be specified optionally
    
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
    
    # parse sections of a page
    
    params = {
        'action': 'parse',
        'page': page,
        'prop': 'sections',
        'format': 'json'
    }
    
    return requests.get(url, headers=headers, params=params, verify=False).json()

def get_section_index(section, page_sections):
    
    # get section index with respect to the page
    
    return next((
        d for d in page_sections
        if section.strip() in d.get('line').lower().strip()
    ), None)['index']

def parse_iwlinks(page_title, url=api_endpoint, headers=host_wiki, section_index=None):
    
    # parse interwiki links in page or section
    # primarily used to parse usernames in various sections
    
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
    
    # extract mentioned Pharicator tickets
    # example: T343301
    
    pattern = r'\b(T\d+)\b'
    return re.findall(pattern, blob)

def extract_usernames_from_parser(api_response):
    
    # extract user names from intrawiki links parse output
    # checks for match to either User: or User talk:
    
    userlinks = api_response['parse']['links']
    usernames = set() 
    
    for link in userlinks:
        if link['*'].startswith('User:'):
            usernames.add(link['*'][5:])
        elif link['*'].startswith('User talk:'):
            usernames.add(link['*'][10:])
    
    return list(usernames)

def extract_proposals(text):
    
    # extract proposal titles of proposals transcluded on a Category page
    # example {{proposal_name}}
    # the actual content of the proposals is on a seperate page
    # format was followed from 2017
    
    pattern = r'{{:([^}]+)}}'
    matches = re.findall(pattern, text)
    return [m for m in matches if 'Category header' not in m]

def extract_proposer_username(text):
    
    # extract username of proposals
    # checks for various patterns that were iteratively improved
    # the proposal section may also contain signatures for other users, which wiki link parser unusable
    
    optional_chars = r"(?:&mdash;|--|→)?\s*"
    
    pattern1 = rf"'''Proposer''':.*?{optional_chars}(?:(?:en:)?User(?:_?talk)?|User talk):(.*?)(?=[\|\[])"
    
    pattern2 = rf"\|\s*proposer\s*=\s*{optional_chars}\[\[User:(.*?)(?=[\|\[])"
    
    match1 = re.search(pattern1, text)
    if match1:
        return match1.group(1).strip()

    elif re.search(pattern2, text):
        return match2.group(1).strip()

    else:
        return None
    
def extract_usernames_from_text(blob):
    
    # extract names from wikitext
    
    pattern = r'\[\[User:([^\]|]*)'
    matches = re.findall(pattern, blob)
    return list(set([match.strip() for match in matches]))

def split_sections_l2(wikitext):
    
    # split sections at level 2 wiki heading
    # example: == Section Name ==
    
    sections = re.split(r'==[^=]+==', wikitext)[1:]
    return sections

def extract_reject_reason(text):
    
    # extract reason for rejected proposals
    
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
    
    # in some cases, proposals get re-titled 
    # the original link is actually a redirect
    # gets the current name of the proposal
    
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
    
    old_title =  (
        wmf.mariadb.run(
            plinks_query
            .format(
                PAGE_TITLE=proposal.replace(' ', '_'), 
                SURVEY_TITLE=get_title(year, 'main_page').replace(' ', '_')
            ), 
            dbs='metawiki')
    )
        
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
    
    """
    Inputs
    ------
    page: str
        - content of the page of to be parsed
        - for this case, page representing a CWS category, containing proposals as level-2 sections
    
    year: int
        only 2015 or 2016 are allowed
    
    Returns
    -------
    dict
        with section index, containing a dict of
            - proposal title
            - index of discussion section (only for 2016)
            - index of votes section
        the section indices are later used to get wikitext of specific sections on a page
    """
    
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
    
    """
    Input
    -----
    wish_text: str
        raw wiki-text of a proposal
        
    Returns
    -------
    tuple
        - wiki-text of proposal section
        - wiki-text of discussion and voting section
    """
    
    splits = re.split('{{collapse top', wish_text)
    discussion_splits = re.split('collapse bottom}}', splits[1])
    return splits[0], discussion_splits[0]

def convert_errors_to_strings(dictionary):
    
    # converts any error type values to string with error text

    for year, data in dictionary.items():
        if isinstance(data, dict):

            for key, value in data.items():
                if isinstance(value, dict) and 'error' in value:

                    value['error'] = str(value['error'])
                elif isinstance(value, str):
                    data[key] = str(value)
    return dictionary