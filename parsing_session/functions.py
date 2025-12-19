from bs4 import BeautifulSoup
import re
from datetime import datetime
from typing import Dict, List, Optional
import unicodedata


def clean_text(text: str, remove_emojis: bool = False) -> str:
    """
    Nettoyer le texte en gérant émoji et symboles chelous
    
    Args:
        text: Texte à nettoyer
        remove_emojis: Si True, supprime les emojis
        
    Returns:
        Texte cleaned
    """
    if not text:
        return text
    
    try:

        text = unicodedata.normalize('NFC', text)
        
        if remove_emojis:
            # Supprimer les emojis et symboles chelous
            emoji_pattern = re.compile(
                "["
                "\U0001F600-\U0001F64F" 
                "\U0001F300-\U0001F5FF"
                "\U0001F680-\U0001F6FF" 
                "\U0001F1E0-\U0001F1FF" 
                "\U00002702-\U000027B0"  
                "\U000024C2-\U0001F251"  
                "]+", flags=re.UNICODE
            )
            text = emoji_pattern.sub('', text)
        

        text = re.sub(r'\s+', ' ', text)
        
        # Suppr espaces 
        text = text.strip()
        
        return text
        
    except (UnicodeEncodeError, UnicodeDecodeError) as e:

        try:

            text = text.encode('utf-8', errors='ignore').decode('utf-8', errors='ignore')
            text = re.sub(r'\s+', ' ', text).strip()
            return text
        except Exception:

            return ""


def parse_deliveroo_html(html_file_path: str) -> Dict:
    """
    Parse un fichier et fait l'extract 
    
    Args:
        html_file_path: Chemin vers le fichier HTML
        
    Returns:
        Dictionnaire contenant toutes les infos parsées
    """
    try:
        with open(html_file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
    except UnicodeDecodeError:

        with open(html_file_path, 'r', encoding='latin-1') as f:
            html_content = f.read()
            html_content = html_content.encode('latin-1').decode('utf-8', errors='ignore')
    
    soup = BeautifulSoup(html_content, 'html.parser')
    

    filename = html_file_path.split('/')[-1]
    date_info = extract_date_from_filename(filename)
    
    return {
        'date': date_info,
        'restaurant': extract_restaurant_info(soup),
        'client': extract_client_info(soup),
        'commande': extract_order_info(soup),
        'articles': extract_items(soup),
        'totaux': extract_totals(soup)
    }


def extract_date_from_filename(filename: str) -> Optional[Dict]:
    """
    Extrait la date et l'heure 
    """

    pattern = r'(\w+)_(\d+)_(\w+)_(\d+)_(\d+)_(\d+)_(\d+)_\.html'
    match = re.search(pattern, filename)
    
    if match:
        jour_semaine, jour, mois_str, annee, heure, minute, seconde = match.groups()
 
        mois_map = {
            'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
            'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
        }
        
        try:
            mois = mois_map.get(mois_str, 1)
            date_obj = datetime(
                int(annee), mois, int(jour),
                int(heure), int(minute), int(seconde)
            )
            return {
                'raw': date_obj.strftime('%Y-%m-%d %H:%M:%S'),
                'datetime': date_obj,
                'jour_semaine': jour_semaine,
                'date': date_obj.strftime('%Y-%m-%d'),
                'heure': date_obj.strftime('%H:%M:%S')
            }
        except (ValueError, KeyError):
            return None
    return None


def parse_address_parts(address_lines: List[str]) -> Dict:
    """
    Parse une liste de lignes d'adresse
    
    Args:
        address_lines: Liste des lignes d'adresse
        
    Returns:
        Dictionnaire avec 'address', 'city', 'postal_code'
    """
    result = {
        'address': None,
        'city': None,
        'postal_code': None
    }
    
    if not address_lines:
        return result
    

    if len(address_lines) > 0:
        result['address'] = clean_text(address_lines[0])

    postal_pattern = r'(\d{5})'
    for line in address_lines[1:]: 
        match = re.search(postal_pattern, line)
        if match:
            result['postal_code'] = match.group(1)

            city_match = re.search(r'\d{5}([A-Za-z\s]+)$', line)
            if city_match:
                result['city'] = city_match.group(1).strip()
            break
    
    if not result['city']:
        for line in address_lines[1:]:  
            cleaned_line = clean_text(line)
            if not re.search(postal_pattern, cleaned_line):

                if re.match(r'^[A-Za-z\s]+$', cleaned_line):
                    result['city'] = cleaned_line
                    break
    
    return result


def extract_restaurant_info(soup: BeautifulSoup) -> Dict:
    """
    Extrait les infos du restaurant
    """
    restaurant_info = {
        'nom': None,
        'address': None,
        'city': None,
        'postal_code': None,
        'telephone': None
    }
    
    tables = soup.find_all('table', class_='fluid')
    for table in tables:
        p_tags = table.find_all('p', style=re.compile(r'font-weight:bolder'))
        if p_tags:
            text = clean_text(p_tags[0].get_text(strip=True))
            if text and len(text) < 100:  

                if 'align="left"' in str(table) or not 'align="right"' in str(table):
                    restaurant_info['nom'] = text
                    address_lines = []
                    next_ps = table.find_all('p', style=re.compile(r'color:#828585'))
                    for p in next_ps:
                        addr_part = clean_text(p.get_text(strip=True))
                        if addr_part and not addr_part.startswith('+'):
                            address_lines.append(addr_part)
                        elif addr_part and addr_part.startswith('+'):
                            restaurant_info['telephone'] = addr_part
                    
                    address_parts = parse_address_parts(address_lines)
                    restaurant_info.update(address_parts)
                    break
    
    return restaurant_info


def extract_client_info(soup: BeautifulSoup) -> Dict:
    """
    Extrait les infos du client
    """
    client_info = {
        'nom': None,
        'address': None,
        'city': None,
        'postal_code': None,
        'telephone': None
    }
    
    tables = soup.find_all('table', class_='fluid')
    for table in tables:
        if 'align="right"' in str(table) or 'text-align:right' in str(table):
            p_tags = table.find_all('p', style=re.compile(r'font-weight:bolder'))
            if p_tags:
                nom = clean_text(p_tags[0].get_text(strip=True))
                if nom:
                    client_info['nom'] = nom
                    address_lines = []
                    next_ps = table.find_all('p', style=re.compile(r'color:#828585'))
                    for p in next_ps:
                        addr_part = clean_text(p.get_text(strip=True))
                        if addr_part and not addr_part.startswith('+'):
                            address_lines.append(addr_part)
                        elif addr_part and addr_part.startswith('+'):
                            client_info['telephone'] = addr_part
                    
                    address_parts = parse_address_parts(address_lines)
                    client_info.update(address_parts)
                    break
    
    if not client_info['nom']:
        h2_tags = soup.find_all('h2')
        for h2 in h2_tags:
            text = clean_text(h2.get_text(strip=True))
            if 'Excellent choix' in text:
                nom = clean_text(text.replace('Excellent choix,', '').strip())
                client_info['nom'] = nom
                break
    
    return client_info


def extract_order_info(soup: BeautifulSoup) -> Dict:
    """
    Extrait les infos de la commande
    """
    order_info = {
        'numero': None
    }
    
    h2_tags = soup.find_all('h2')
    for h2 in h2_tags:
        text = clean_text(h2.get_text(strip=True))
        match = re.search(r'Commande n[°\s]+(\d+)', text, re.IGNORECASE)
        if match:
            order_info['numero'] = match.group(1)
            break
    
    if not order_info['numero']:
        try:
            all_text = clean_text(soup.get_text())
            match = re.search(r'num[ée]ro de commande.*?est[:\s]+(\d+)', all_text, re.IGNORECASE)
            if match:
                order_info['numero'] = match.group(1)
        except Exception:
            pass
    
    return order_info


def extract_items(soup: BeautifulSoup) -> List[Dict]:
    """
    Extrait les articles commandés
    """
    items = []
    
    list_item_table = soup.find('table', role='listitem')
    
    if not list_item_table:
        return items
    
    rows = list_item_table.find_all('tr')
    
    for row in rows:
        item = {
            'quantite': None,
            'nom': None,
            'options': [],
            'prix': None
        }
        
        cells = row.find_all('td')
        if len(cells) < 2:
            continue
        
        qty_cell = cells[0] if len(cells) > 0 else None
        name_cell = cells[1] if len(cells) > 1 else None
        price_cell = cells[2] if len(cells) > 2 else None
        
        if qty_cell:
            qty_p = qty_cell.find('p')
            if qty_p:
                qty_text = clean_text(qty_p.get_text(strip=True))
                match = re.search(r'^(\d+)x$', qty_text)
                if match:
                    item['quantite'] = int(match.group(1))
        
        if name_cell:
            name_p = name_cell.find('p', style=re.compile(r'color:#000001'))
            if name_p:
                nom_text = clean_text(name_p.get_text(strip=True))
                if nom_text and not re.match(r'^\d+x$', nom_text) and len(nom_text) > 3:
                    item['nom'] = nom_text
                    
                    option_ps = name_cell.find_all('p', style=re.compile(r'color:#828585'))
                    for p in option_ps:
                        option_text = clean_text(p.get_text(strip=True))
                        if option_text and option_text != item['nom'] and len(option_text) > 0:
                            item['options'].append(option_text)
        
        if price_cell:
            price_p = price_cell.find('p', style=re.compile(r'text-align:right'))
            if price_p:
                price_text = clean_text(price_p.get_text(strip=True))
                match = re.search(r'€?\s*([\d,\.]+)\s*[€€]?', price_text)
                if match:
                    price_str = match.group(1).replace(',', '.')
                    try:
                        item['prix'] = float(price_str)
                    except ValueError:
                        pass
        
        if item['nom']:
            items.append(item)
    
    return items


def extract_totals(soup: BeautifulSoup) -> Dict:
    """
    Extrait les totaux 
    """
    totals = {
        'sous_total': None,
        'frais_livraison': None,
        'pourboire': None,
        'credit': None,
        'total': None
    }
    
    all_trs = soup.find_all('tr')
    
    for tr in all_trs:
        tds = tr.find_all('td')
        if len(tds) >= 2:
            label_p = tds[0].find('p')
            price_p = tds[1].find('p')
            
            if label_p and price_p:
                label_text = clean_text(label_p.get_text(strip=True))
                price_text = clean_text(price_p.get_text(strip=True))
                
                price_match = re.search(r'€?\s*([\d,\.]+)', price_text)
                if price_match:
                    price_str = price_match.group(1).replace(',', '.')
                    try:
                        price_value = float(price_str)
                        
                        if 'Sous-total' in label_text:
                            totals['sous_total'] = price_value
                        elif 'Frais de livraison' in label_text:
                            totals['frais_livraison'] = price_value
                        elif 'Pourboire' in label_text:
                            totals['pourboire'] = price_value
                        elif 'Crédit' in label_text:
                            totals['credit'] = price_value
                        elif 'Total' in label_text and ('class="total"' in str(label_p) or 'font-size:34px' in str(label_p)):
                            totals['total'] = price_value
                    except ValueError:
                        pass
    
    return totals


def generate_order_json(html_file_path: str) -> Dict:
    """
    Parse un fichier HTML et génère un JSON
    
    Args:
        html_file_path: Chemin vers le fichier HTML
        
    Returns:
        Dictionnaire JSON 
        - Order: number, total_paid, delivery_fee, datetime
        - Order Items: name, price, quantity
        - Restaurant: name, address, city, postal_code, phone_number
        - Customer: name, address, city, postal_code, phone_number
    """
    parsed_data = parse_deliveroo_html(html_file_path)
    
    json_data = {
        'Order': {
            'number': parsed_data['commande']['numero'],
            'total_paid': parsed_data['totaux']['total'],
            'delivery_fee': parsed_data['totaux']['frais_livraison'],
            'datetime': parsed_data['date']['raw'] if parsed_data['date'] else None
        },
        'Order Items': [
            {
                'name': item['nom'],
                'price': item['prix'],
                'quantity': item['quantite']
            }
            for item in parsed_data['articles']
        ],
        'Restaurant': {
            'name': parsed_data['restaurant']['nom'],
            'address': parsed_data['restaurant']['address'],
            'city': parsed_data['restaurant']['city'],
            'postal_code': parsed_data['restaurant']['postal_code'],
            'phone_number': parsed_data['restaurant']['telephone']
        },
        'Customer': {
            'name': parsed_data['client']['nom'],
            'address': parsed_data['client']['address'],
            'city': parsed_data['client']['city'],
            'postal_code': parsed_data['client']['postal_code'],
            'phone_number': parsed_data['client']['telephone']
        }
    }
    
    return json_data

