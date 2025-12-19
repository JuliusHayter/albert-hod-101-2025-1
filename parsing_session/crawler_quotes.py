import requests
from bs4 import BeautifulSoup
from typing import List, Dict
import time
import json


def scrape_quotes_from_page(url: str) -> tuple[List[Dict], str]:
    """
    Scrape toutes les citations d'une page
    
    Args:
        url: URL de la page à scraper
        
    Returns:
        Tuple contenant:
        - Liste de dictionnaires avec les citations (texte, auteur, tags)
        - URL de la page suivante 
    """
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        quotes = []
        
        quote_elements = soup.find_all('div', class_='quote')
        
        for quote_element in quote_elements:
            quote_data = {
                'text': None,
                'author': None,
                'tags': []
            }
            
            text_element = quote_element.find('span', class_='text')
            if text_element:
                quote_data['text'] = text_element.get_text(strip=True)
            
            author_element = quote_element.find('small', class_='author')
            if author_element:
                quote_data['author'] = author_element.get_text(strip=True)
            
            tags_container = quote_element.find('div', class_='tags')
            if tags_container:
                tag_elements = tags_container.find_all('a', class_='tag')
                quote_data['tags'] = [tag.get_text(strip=True) for tag in tag_elements]
            
            if quote_data['text']:
                quotes.append(quote_data)
        
        next_link = None
        next_element = soup.find('li', class_='next')
        if next_element:
            next_anchor = next_element.find('a')
            if next_anchor and next_anchor.get('href'):
                next_href = next_anchor.get('href')
                if next_href.startswith('/'):
                    base_url = '/'.join(url.split('/')[:3])
                    next_link = base_url + next_href
                else:
                    next_link = next_href
        
        return quotes, next_link
        
    except requests.RequestException as e:
        print(f"Erreur lors de la requête à {url}: {str(e)}")
        return [], None
    except Exception as e:
        print(f"Erreur lors du parsing de {url}: {str(e)}")
        return [], None


def crawl_all_quotes(start_url: str) -> List[Dict]:
    """
    Crawl toutes les pages du site en suivant automatiquement la pagination
    
    Args:
        start_url: URL de départ (première page)
        
    Returns:
        Liste de tous les dictionnaires de citations trouvées
    """
    all_quotes = []
    current_url = start_url
    page_count = 0
    
    print(f"Démarrage du crawl à partir de: {start_url}")
    
    while current_url:
        page_count += 1
        print(f"Scraping page {page_count}: {current_url}")
        
        quotes, next_url = scrape_quotes_from_page(current_url)
        
        if quotes:
            all_quotes.extend(quotes)
            print(f"  → {len(quotes)} citations trouvées sur cette page")
        else:
            print(f"  → Aucune citation trouvée sur cette page")
        
        current_url = next_url
        
        if current_url:
            time.sleep(0.5)
    
    print(f"\nCrawl terminé! Total: {len(all_quotes)} citations sur {page_count} pages")
    return all_quotes


if __name__ == '__main__':
    base_url = 'https://quotes.toscrape.com/'
    output_file = 'quotes.json'
    
    all_quotes = crawl_all_quotes(base_url)
    
    if all_quotes:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_quotes, f, indent=2, ensure_ascii=False)
        
        print(f"\n✓ {len(all_quotes)} citations sauvegardées dans '{output_file}'")
        
        print("\n" + "="*60)
        print("Exemple :")
        print("="*60)
        example = all_quotes[0]
        print(f"Texte: {example['text']}")
        print(f"Auteur: {example['author']}")
        print(f"Tags: {example['tags']}")
        print("="*60)
    else:
        print("Aucune citation extraite wtf")

