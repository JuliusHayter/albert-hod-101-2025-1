import requests
from bs4 import BeautifulSoup
from typing import List, Dict
import time


def scrape_quotes_from_page(url: str) -> tuple[List[Dict], str, List[str]]:
    """
    Scrape toutes les citations d'une page donnée
    
    Args:
        url: URL de la page à scraper
        
    Returns:
        Tuple contenant:
        - Liste de dictionnaires avec les citations (texte, auteur, tags)
        - URL de la page suivante (ou None si pas de pagination)
        - Liste des top ten tags
    """
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        quotes = []
        
        # Trouver tous les éléments de citation
        quote_elements = soup.find_all('div', class_='quote')
        
        for quote_element in quote_elements:
            quote_data = {
                'text': None,
                'author': None,
                'tags': []
            }
            
            # Extraire le texte de la citation
            text_element = quote_element.find('span', class_='text')
            if text_element:
                quote_data['text'] = text_element.get_text(strip=True)
            
            # Extraire l'auteur
            author_element = quote_element.find('small', class_='author')
            if author_element:
                quote_data['author'] = author_element.get_text(strip=True)
            
            # Extraire les tags
            tags_container = quote_element.find('div', class_='tags')
            if tags_container:
                tag_elements = tags_container.find_all('a', class_='tag')
                quote_data['tags'] = [tag.get_text(strip=True) for tag in tag_elements]
            
            # Ajouter seulement si on a au moins le texte
            if quote_data['text']:
                quotes.append(quote_data)
        
        # Extraire les top ten tags
        top_ten_tags = []
        # Chercher le h2 "Top Ten tags"
        h2_tags = soup.find_all('h2')
        for h2 in h2_tags:
            if 'Top Ten tags' in h2.get_text() or 'Top Ten' in h2.get_text():
                # Trouver tous les spans avec class="tag-item" après ce h2
                tag_items = h2.find_next_siblings('span', class_='tag-item')
                for tag_item in tag_items:
                    tag_link = tag_item.find('a', class_='tag')
                    if tag_link:
                        top_ten_tags.append(tag_link.get_text(strip=True))
                break
        
        # Trouver le lien "Next" pour la pagination
        next_link = None
        next_element = soup.find('li', class_='next')
        if next_element:
            next_anchor = next_element.find('a')
            if next_anchor and next_anchor.get('href'):
                next_href = next_anchor.get('href')
                # Construire l'URL complète si c'est un lien relatif
                if next_href.startswith('/'):
                    base_url = '/'.join(url.split('/')[:3])
                    next_link = base_url + next_href
                else:
                    next_link = next_href
        
        return quotes, next_link, top_ten_tags
        
    except requests.RequestException as e:
        print(f"Erreur lors de la requête à {url}: {str(e)}")
        return [], None
    except Exception as e:
        print(f"Erreur lors du parsing de {url}: {str(e)}")
        return [], None


def crawl_all_quotes(start_url: str) -> tuple[List[Dict], List[str]]:
    """
    Crawl toutes les pages du site en suivant automatiquement la pagination
    
    Args:
        start_url: URL de départ (première page)
        
    Returns:
        Tuple contenant:
        - Liste de tous les dictionnaires de citations trouvées
        - Liste des top ten tags (extraits de la première page)
    """
    all_quotes = []
    top_ten_tags = []
    current_url = start_url
    page_count = 0
    
    print(f"Démarrage du crawl à partir de: {start_url}")
    
    while current_url:
        page_count += 1
        print(f"Scraping page {page_count}: {current_url}")
        
        quotes, next_url, page_top_tags = scrape_quotes_from_page(current_url)
        
        if quotes:
            all_quotes.extend(quotes)
            print(f"  → {len(quotes)} citations trouvées sur cette page")
        else:
            print(f"  → Aucune citation trouvée sur cette page")
        
        # Extraire les top ten tags de la première page
        if page_count == 1 and page_top_tags:
            top_ten_tags = page_top_tags
            print(f"  → Top ten tags trouvés: {len(top_ten_tags)} tags")
        
        # Passer à la page suivante
        current_url = next_url
        
        # Petite pause pour être respectueux avec le serveur
        if current_url:
            time.sleep(0.5)
    
    print(f"\nCrawl terminé! Total: {len(all_quotes)} citations sur {page_count} pages")
    return all_quotes, top_ten_tags


if __name__ == '__main__':
    # URL de départ
    base_url = 'https://quotes.toscrape.com/'
    
    # Lancer le crawl
    all_quotes, top_ten_tags = crawl_all_quotes(base_url)
    
    # Afficher un exemple de résultat
    if all_quotes:
        print("\n" + "="*60)
        print("Exemple de citation extraite:")
        print("="*60)
        example = all_quotes[0]
        print(f"Texte: {example['text']}")
        print(f"Auteur: {example['author']}")
        print(f"Tags: {example['tags']}")
        print("="*60)
        
        print(f"\nTotal de citations stockées: {len(all_quotes)}")
        
        # Afficher les top ten tags
        if top_ten_tags:
            print("\n" + "="*60)
            print("Top Ten Tags:")
            print("="*60)
            for i, tag in enumerate(top_ten_tags, 1):
                print(f"{i}. {tag}")
            print("="*60)
        
        # Afficher quelques statistiques
        unique_authors = set(quote['author'] for quote in all_quotes if quote['author'])
        print(f"\nNombre d'auteurs uniques: {len(unique_authors)}")
        
        all_tags = []
        for quote in all_quotes:
            all_tags.extend(quote['tags'])
        unique_tags = set(all_tags)
        print(f"Nombre de tags uniques: {len(unique_tags)}")
    else:
        print("Aucune citation n'a été extraite.")

