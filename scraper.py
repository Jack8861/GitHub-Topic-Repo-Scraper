import requests
from bs4 import BeautifulSoup
import os
import pandas as pd

def scrape_topics():
    topics_url = "https://github.com/topics" #url for the page we want to scrape ( check it out )
    #download the page
    response = requests.get(topics_url)
    if response.status_code != 200: #200 response means the page responded and we got the page
        raise Exception("Failed to to load page {}".format(topics_url))
        
    page_contents = response.text
    #parse the html
    doc = BeautifulSoup(page_contents, 'html.parser')
    
    #get the respective information using the doc
    topic_dict = {
        'title': get_topic_titles(doc),
        'description': get_topic_desc(doc),
        'url': get_topic_link(doc),
    }
    #convert the dictionary into a pandas DataFrame
    topics_df = pd.DataFrame(topic_dict)
    
    return topics_df
    
def get_topic_titles(doc):
    # find the paragraph tags with the specified class name
    select_topic_class = "f3 lh-condensed mb-0 mt-1 Link--primary"
    topic_title_tags = doc.find_all('p',{'class':select_topic_class})
    
    topic_titles = []

    for tag in topic_title_tags: #interate through each of the tags and extract the text inside ( title )
        topic_titles.append(tag.text)
        
    return topic_titles
    
def get_topic_desc(doc):
    # find the paragraph tags with the specified class name
    select_desc_class = "f5 color-text-secondary mb-0 mt-1"
    topic_desc_tags = doc.find_all('p',{'class':select_desc_class})
    
    topic_descriptions = []

    for tag in topic_desc_tags: #interate through each of the tags and extract the text inside ( description )
        topic_descriptions.append(tag.text.strip())
        
    return topic_descriptions
    
def get_topic_link(doc):
    # find the a tags with the specified class name
    select_link_class = "d-flex no-underline"
    topic_link_tags = doc.find_all('a', {'class':select_link_class})
    
    topic_urls = []
    base_url = 'https://github.com'
    for tag in topic_link_tags: #interate through each of the tags and extract the text inside ( link )
        topic_urls.append(base_url + tag['href'])
    
    return topic_urls
    
def get_topic_page(topic_url):
    # download the page
    response = requests.get(topic_url)
    if response.status_code != 200:
        raise Exception("Failed to to load page {}".format(topic_url))
    # parse html
    topic_doc = BeautifulSoup(response.text, 'html.parser')
    
    return topic_doc
    
def get_topic_repos(topic_doc):
    #classes of elements we want to scrape
    repo_class = "f3 color-text-secondary text-normal lh-condensed"
    star_class = 'social-count float-none'
    
    #find all the respective tags
    repo_tags = topic_doc.find_all('h1', class_=repo_class)
    star_tags = topic_doc.find_all('a', {'class': star_class})
    
    #create a dictonary to store the information we are about to extract
    topic_repos_dict = {
        'username':[],
        'repo_name': [],
        'stars': [],
        'repo_url': []
        }    
    
    for i in range(len(repo_tags)): #iterate through the tags
        repo_info = get_repo_info(repo_tags[i], star_tags[i]) # call function which gives a nested list of information we want
        
        topic_repos_dict['username'].append(repo_info[0]) # 1st inner list element has username
        topic_repos_dict['repo_name'].append(repo_info[1]) # 2nd inner list element has repository name
        topic_repos_dict['stars'].append(repo_info[2])     # 3rd inner list element has stars gotten
        topic_repos_dict['repo_url'].append(repo_info[3])  # 4th inner list element has repository url
    
    return pd.DataFrame(topic_repos_dict)
    
    
def get_repo_info(h1_tag, star_tag):
    # 2 a tag have the usename and repository name respectively so extract them
    a_tags = h1_tag.find_all('a')
    base_url = 'https://github.com'
    
    username = a_tags[0].text.strip()
    repo_name = a_tags[1].text.strip()
    repo_url = base_url + a_tags[1]['href'] # a relative path is mentioned in a tag so we combine it with base url
    
    # the stars are in string format eg: '76k' we want to convert it to 76000
    stars = parse_star_count(star_tag.text.strip()) # function to extract stars as type integer
    
    return username, repo_name, repo_url, stars
    
    
    
def parse_star_count(stars_str):
    stars_str = stars_str.strip()
    if stars_str[-1] == 'k':
        return int(float(stars_str[:-1]) * 1000)
    return int(stars_str)
        
        
def scrape_topics_repos():
    try:
        dir_name = "./top_topic_repos" #directory store the csv files in
        
        if os.path.isdir('top_topic_repos'): #check if it exists
            print('top_topic_repos directory exists')
        else: #create directory if it doesn't exist
            return
            os.mkdir(dir_name)
    except OSError:
        print ("Creation of the directory %s failed" % dir_name)
        
    print("Scraping list of topics")
    topics_df = scrape_topics() # function from first part
    
    for index, row in topics_df.iterrows(): # iterate through the topic infos
        print("scraping top repositories for {}".format(row['title']))
        scrape_topic(row['url'], row['title'], dir_name) # helper function to call the other functions
        
        
        
def scrape_topic(topic_url, topic_name, dir_name):
    # filename
    floc = dir_name + '/' + topic_name + ".csv"
    if os.path.exists(floc): # check if it exists and don't scrape if it does
        print("The file {}.csv already exists :)".format(topic_name))
        return
    #get the dataframe for information of respositories of each topic
    topic_df = get_topic_repos(get_topic_page(topic_url))
    #create a csv file of the dataframe
    topic_df.to_csv(floc,index=None)
    
    
if __name__ == '__main__':
    scrape_topics_repos()