# Módulos externos
import pandas as pd

class Dados:

    def __init__(self):
        super().__init__()
        self.padrao_colunas = [
            "name",
            "product_url",
            "part_number",
            "brand_name",
            "category",
            "price",
            "gross_weight",
            "width",
            "length",
            "warranty",
            "material",
            "photo_url",
            "stock_quantity"
        ]
    
    def transforma_dados(self,
                        name: str,
                        product_url: str,
                        category: str,
                        part_number: str,
                        brand_name: str,
                        price: str,
                        gross_weight: str,
                        dimensions: str,
                        warranty: str,
                        main_material: str,
                        url_photo: str,
                        stock_quantity: str,
                        ) -> pd.DataFrame:

        preposicoes = {"de", "da", "do"}
        palavras = name.split()
        palavras_filtradas = [
        p for p in palavras
        if p[0].isupper() or p.lower() in preposicoes
        ]
        name = " ".join(palavras_filtradas).upper()
        brand_name = brand_name.upper()
        valores = dimensions.split(" x ")
        width = valores[0]
        length = valores[1]
        width = float(width.replace("cm", "").replace(",", "."))
        length = float(length.replace("cm", "").replace(",", "."))
        price = float(price.replace("R$ ", "").replace(".", "").replace(",", "."))
        gross_weight = float(gross_weight.replace("kg", "").replace(",", "."))
        if stock_quantity.lower() != 'fora de estoque':
            try:
                stock_quantity = int(stock_quantity.replace(" unidades em estoque", "").strip())
            except:
                stock_quantity = int(stock_quantity.replace("Estoque baixo (", "").replace(" unidades)", "").strip())
        else:
            stock_quantity = int(0)
        warranty = warranty.replace(" meses", "")
        part_number = part_number.split("Part Number: ")[1].strip()
        main_material = main_material.strip()

        df_transformado = pd.DataFrame({
            "name": [name],
            "product_url": [product_url],
            "part_number": [part_number],
            "brand_name": [brand_name],
            "category": [category],
            "price": [price],
            "gross_weight": [gross_weight],
            "width": [width],
            "length": [length],
            "warranty": [warranty],
            "material": [main_material],
            "photo_url": [url_photo],
            "stock_quantity": [stock_quantity]
        })

        return df_transformado

    def refina_dados(self, df: pd.DataFrame) -> pd.DataFrame:

        df.drop_duplicates(inplace=True)
        df['price'] = pd.to_numeric(df['price'], errors='coerce').astype('float64')
        df['gross_weight'] = pd.to_numeric(df['gross_weight'], errors='coerce').astype('float64')
        df['width'] = pd.to_numeric(df['width'], errors='coerce').astype('float64')
        df['length'] = pd.to_numeric(df['length'], errors='coerce').astype('float64')
        df['stock_quantity'] = pd.to_numeric(df['stock_quantity'], errors='coerce').astype('int64')

        return df
