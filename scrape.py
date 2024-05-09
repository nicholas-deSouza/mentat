import requests
from bs4 import BeautifulSoup
import csv
import re

def get_iframe_link(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Navigate through divs to reach the iframe
        main_wrapper = soup.find('div', class_='main wrapper')
        
        if main_wrapper:
            inner_column = main_wrapper.find('div', id='inner_column')
            
            if inner_column:
                game_view = inner_column.find('div', id=re.compile(r'^view_html_game_'))
                
                if game_view:
                    html_embed = game_view.find('div', id=re.compile(r'^html_embed_'))
                    
                    if html_embed:
                        game_frame = html_embed.find('div', class_='game_frame game_pending') or html_embed.find('div', class_='game_frame game_pending start_maximized')
                        
                        if game_frame:
                            iframe_placeholder = game_frame.find('div', class_='iframe_placeholder')
                            if iframe_placeholder:
                                iframe_html = iframe_placeholder.get('data-iframe')
                                iframe_soup = BeautifulSoup(iframe_html, 'html.parser') if iframe_html else None
                                iframe = iframe_soup.find('iframe') if iframe_soup else None
                                return iframe['src'] if iframe and 'src' in iframe.attrs else 'Iframe src not found'
        return 'Appropriate div not found'
    except requests.RequestException as e:
        return str(e)

def scrape_itch_io(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extracting game title
        game_title = soup.find('h1').text.strip() if soup.find('h1') else 'Title not found'

        # Creator name and URL
        creator_tag = soup.find('span', class_='mobile_label')
        creator_name = creator_tag.text.strip() if creator_tag else 'Creator not found'
        creator_url_tag = soup.find('a', class_='action_btn view_more')
        creator_url = creator_url_tag['href'] if creator_url_tag else 'Creator URL not found'

        # Genre
        more_info_button = soup.find('a', class_='toggle_info_btn')
        genres = []
        if more_info_button:
            info_table = more_info_button.find_next('table')
            if info_table:
                rows = info_table.find_all('tr')
                for row in rows:
                    cells = row.find_all('td')
                    if cells and 'Genre' in cells[0].text:
                        genre_links = cells[1].find_all('a')
                        genres = [link.text for link in genre_links]
        genre = ', '.join(genres) if genres else 'Genre not identified'

        # Tags
        tags = []
        if more_info_button:
            info_table = more_info_button.find_next('table')
            if info_table:
                rows = info_table.find_all('tr')
                for row in rows:
                    cells = row.find_all('td')
                    if cells and 'Tags' in cells[0].text:
                        tag_links = cells[1].find_all('a')
                        tags = [link.text for link in tag_links]
        tags_str = ', '.join(tags) if tags else 'No tags'

        # Description
        description_tag = soup.find('meta', property='og:description')
        description = description_tag['content'].strip() if description_tag else 'Description not found'

        # Iframe Link
        iframe_link = get_iframe_link(url)

        return {
            'Game Title': game_title,
            'Itch Landing Page URL': url,
            'Creator Name': creator_name,
            'Creator Itch URL': creator_url,
            'Genre': genre,
            'Tags': tags_str,
            'Description': description,
            'Play File Itch URL': iframe_link
        }

    except requests.RequestException as e:
        return {'Error': f"Error fetching the page: {e}"}
    except AttributeError:
        return {'Error': "Necessary data not found on page."}

def scrape_multiple_links(urls):
    results = []
    for url in urls:
        result = scrape_itch_io(url)
        results.append(result)
    return results

def write_to_csv(game_data):
    keys = game_data[0].keys()
    with open('game_data.csv', 'w', newline='') as output_file:
        dict_writer = csv.DictWriter(output_file, keys)
        dict_writer.writeheader()
        dict_writer.writerows(game_data)

# Example usage:
urls = [
    "https://mslivo.itch.io/sandtrix",
    "https://husbandogoddess.itch.io/intoxicating",
    "https://coeluvr.itch.io/crown-of-ashes-and-flames",  # Add as many URLs as you want
]

game_info_list = scrape_multiple_links(urls)
write_to_csv(game_info_list)
print("Data has been written to 'game_data.csv'")
