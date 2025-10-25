# Módulos nativos
import os
import pandas as pd

# Módulos externos
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException

# Módulos internos
from dados import Dados
from banco import Banco

class Coleta(Banco, Dados):

    def __init__(self, PATH_DATA, USUARIO, SENHA, HOST, PORTA, DATABASE):
        super().__init__(USUARIO, SENHA, HOST, PORTA, DATABASE, PATH_DATA)
        self.PATH_DATA = PATH_DATA
        self.driver = self.get_webdriver()

    def get_webdriver(self):

        options = Options()
        options.set_preference("browser.cache.disk.enable", False)
        options.set_preference("browser.cache.memory.enable", False)
        options.set_preference("browser.cache.offline.enable", False)
        options.set_preference("network.http.use-cache", False)

        try:
            selenium_host = os.getenv("SELENIUM_HOST", "selenium-firefox")
            driver = webdriver.Remote(
                command_executor=f'http://{selenium_host}:4444/wd/hub',
                options=options
            )
            print("INFO: Conexão com o Selenium (Firefox) estabelecida.")
        except Exception as e:
            print(f"ERRO: Não foi possível conectar ao contêiner do Selenium. {e}")
            print("Verifique se o serviço 'selenium-firefox' está rodando.")
            raise e
        
        return driver
    
    def acessa_site(self) -> None:

        self.driver.get("https://testdata.devmka.online/")
        self.driver.maximize_window()
    
    def verifica_numero_pagina_ativa(self) -> int:

        try:

            div_paginacao = WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, "div.mt-12 > nav[aria-label='pagination']"))
            )

            pagina_ativa = div_paginacao.find_element(By.CSS_SELECTOR, "a[aria-current='page']")
            
            if pagina_ativa.text.isdigit():
                return int(pagina_ativa.text)
            else:
                print(f"Texto inesperado na página ativa: '{pagina_ativa.text}'")
                return 1
        except Exception as e:
            print(f"Erro ao verificar número da página ativa: {e}")
            return 1
        
    def verifica_total_paginas(self) -> int:

        ul_paginacao = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "/html/body/div/div[2]/main/section[2]/div/div[2]/nav/ul"))
        )
        li_filhos = ul_paginacao.find_elements(By.TAG_NAME, "li")
        qtd_paginas = int(li_filhos[-2].text)
        return qtd_paginas
        
    def avanca_pagina(self) -> None:

        ul_paginacao = self.driver.find_element(By.CSS_SELECTOR, "ul.flex.flex-row.items-center.gap-1")
        li_filhos = ul_paginacao.find_elements(By.TAG_NAME, "li")

        numero_pagina_ativa = self.verifica_numero_pagina_ativa()
        ultima_pagina = self.verifica_total_paginas()

        try:
            if numero_pagina_ativa < ultima_pagina:
                botao_avancar = li_filhos[-1].find_element(By.TAG_NAME, "a")
                botao_avancar.click()
                WebDriverWait(self.driver, 10).until(
                    EC.text_to_be_present_in_element(
                        (By.CSS_SELECTOR, "a[aria-current='page']"),
                        str(numero_pagina_ativa + 1)
                    )
                )
            else:
                self.encerra_webdriver()
        except Exception as e:
            print(e)

    def itera_grid_pagina(self) -> None:

        df_lista = []
        aba_principal = self.driver.current_window_handle
        cards = self.driver.find_elements(By.CSS_SELECTOR, "div.rounded-lg.border.bg-card")

        for card in cards:
            link_url = None
            try:
                link_element = card.find_element(By.XPATH, ".//a[contains(text(),'Ver Detalhes')]")
                link_url = link_element.get_attribute("href")
                self.driver.execute_script("window.open(arguments[0]);", link_url)
                self.driver.switch_to.window(self.driver.window_handles[1])

                df_pos_coleta = self.coleta_dados(link_url)
                df_pos_coleta.fillna("", inplace=True)
                if not df_pos_coleta.empty:
                    df_pos_coleta = df_pos_coleta[self.padrao_colunas]
                    df_lista.append(df_pos_coleta)

            except StaleElementReferenceException:
                cards = self.driver.find_elements(By.CSS_SELECTOR, "div.rounded-lg.border.bg-card")
                continue

            except Exception as e:
                print(f"Erro na coleta do produto {link_url}: {e}")

            finally:
                if len(self.driver.window_handles) > 1:
                    self.driver.close()
                    self.driver.switch_to.window(aba_principal)

        df = pd.concat(df_lista, ignore_index=True)
        df = self.refina_dados(df)
        try:
            self.sobe_dados_postgresql(df=df)
        except Exception as e:
            print(f"Erro ao enviar dados para o banco: {e}")

        self.avanca_pagina()


    
    def extrai_dados(self) -> None:
        self.acessa_site()

        try:
            xpath_registro_ausencia_produto = '/html/body/div/div[2]/main/section[2]/div/div[2]/h3'
            elemento_ausencia = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.XPATH, xpath_registro_ausencia_produto))
            )
            if elemento_ausencia.text.strip().lower() == "nenhum produto encontrado":
                print("Nenhum produto encontrado no site.")
                self.encerra_webdriver()
                return
        except:
            qtd_paginas = self.verifica_total_paginas()
            for pagina in range(1, qtd_paginas + 1):
                self.itera_grid_pagina()

    def coleta_dados(self, link: str) -> pd.DataFrame:

        xpath_name_product = '//*[@id="root"]/div[2]/main/div[2]/div[2]/h1'
        name_product = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.XPATH, xpath_name_product))).text

        xpath_category = '//*[@id="root"]/div[2]/main/div[2]/div[2]/div[1]'
        category = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.XPATH, xpath_category))).text

        xpath_brand_name = '//*[@id="root"]/div[2]/main/div[2]/div[2]/p[1]'
        brand_name = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.XPATH, xpath_brand_name))).text

        xpath_price = '//*[@id="root"]/div[2]/main/div[2]/div[2]/p[3]'
        price = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.XPATH, xpath_price))).text
        
        xpath_part_number = '//*[@id="root"]/div[2]/main/div[2]/div[2]/p[2]'
        part_number = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.XPATH, xpath_part_number))).text
        
        xpath_stock_quantity = '//*[@id="root"]/div[2]/main/div[2]/div[2]/div[2]/div'
        stock_quantity = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.XPATH, xpath_stock_quantity))).text
        
        xpath_gross_weight = '//*[@id="root"]/div[2]/main/div[2]/div[2]/div[3]/div[2]/ul/li[1]/span[2]'
        gross_weight = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.XPATH, xpath_gross_weight))).text
        
        xpath_dimensions = '//*[@id="root"]/div[2]/main/div[2]/div[2]/div[3]/div[2]/ul/li[2]/span[2]'
        dimensions = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.XPATH, xpath_dimensions))).text
        
        xpath_main_material = '//*[@id="root"]/div[2]/main/div[2]/div[2]/div[3]/div[2]/ul/li[3]/span[2]'
        main_material = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.XPATH, xpath_main_material))).text
        
        xpath_warranty = '//*[@id="root"]/div[2]/main/div[2]/div[2]/div[3]/div[2]/ul/li[4]/span[2]'
        warranty = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.XPATH, xpath_warranty))).text
        
        xpath_url_photo = '//*[@id="root"]/div[2]/main/div[2]/div[1]/div/img'
        url_photo = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.XPATH, xpath_url_photo))).get_attribute("src")
        
        df_transformado = self.transforma_dados(name_product,
                                                link,
                                                category,
                                                part_number,
                                                brand_name,
                                                price,
                                                gross_weight,
                                                dimensions,
                                                warranty,
                                                main_material,
                                                url_photo,
                                                stock_quantity
                                                )

        return df_transformado

    def encerra_webdriver(self):
        self.driver.quit()
