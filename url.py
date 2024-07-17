import requests, time
from bs4 import BeautifulSoup
from datetime import datetime

def fetch_url_inf(url):
    try:
        response = requests.get(url)
        response.raise_for_status() #hata kodlarını kontrol ediyor.

        soup = BeautifulSoup(response.text, "html.parser") 
        # response.text, response html içeriğine gelen yanıtı metin şeklinde tutar. 
        # BeatifulSoap ise html, xml dosyalarını parse ediyor.
        # response.text response değişkeninden gelen html cevabını text şeklinde tutar ve html ile parse eder. 
        # html, lxml, html5lib gibi farklı parser yani ayrıştırıcılarda kullanabiliriz.

        title = soup.find("title").get_text() 
      
        price_tag = soup.find("span", class_="prc-dsc")
        price = price_tag.get_text() if price_tag else "Fiyat Bulunamadı"
        #price_tag.get_text() price_tag değişkeninin içi doluysa iç metnini al demek.

        return price, title
   
    except requests.exceptions.RequestException as e:
        return None, None, f"URL'den içerik alınırken hata oluştu: {e}"
    except AttributeError:
        return None, None, f"Fiyat bulunamadı"

def main():
    url = input("Lütfen URL giriniz: ")

    previous_price = None

    while True:
        current_price, title = fetch_url_inf(url)

        if title and current_price:
            query_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            print(f"Title: {title}")
            print(f"Price: {current_price}")  
            print(f"Query_time: {query_time}") 

            if previous_price and current_price != previous_price:
                print(f"Fiyat Değişikliği oldu!! Eski fiyat: {previous_price}, Yeni fiyat: {current_price}")

            previous_price = current_price
        
        time.sleep(3600)
if __name__ == "__main__":
    main()        
