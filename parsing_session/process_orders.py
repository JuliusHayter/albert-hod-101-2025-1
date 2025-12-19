import os
import json
from functions import generate_order_json


def process_all_orders(input_dir: str = '.', output_file: str = 'all_orders.json'):
    """
    Itère sur tous les fichiers HTML dans le répertoire et crée un JSON combiné
    
    Args:
        input_dir: Répertoire contenant les fichiers HTML (par défaut: répertoire courant)
        output_file: Nom du fichier JSON de sortie (par défaut: 'all_orders.json')
    """
    all_orders = {
        'orders': []
    }
    
    html_files = [f for f in os.listdir(input_dir) if f.endswith('.html')]

    
    

    for i, html_file in enumerate(html_files, 1):
        file_path = os.path.join(input_dir, html_file)
        
        try:

            
            order_data = generate_order_json(file_path)
            
            all_orders['orders'].append(order_data)
            

            
        except Exception as e:
            print(f"  error {html_file}: {str(e)}")
            continue
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_orders, f, indent=2, ensure_ascii=False, default=str)
    



if __name__ == '__main__':
    process_all_orders()

