import collections
import json
import logging
import re
import time

from playwright.sync_api import Page, expect, sync_playwright

logging.basicConfig(level=logging.DEBUG, filename='scraper.log', filemode='w',
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

Category = collections.namedtuple('Category', ['name', 'url'])
SubCategory = collections.namedtuple('SubCategory', ['name', 'url'])
Product = collections.namedtuple('Product',
                                 ['product_id', 'name', 'price', 'description', 'review_count', 'category'])


class EcommerceScraper:

    def __init__(self, url: str, output_file: str, headless: bool = True):
        logging.info("Initializing @EcommerceScraper")
        self.initial_url = url
        self.base_url = re.search(r"(.*://[.\w]+)/\w*", url).group(1)
        self.products = list()
        self.visited = set()
        self.output_file = output_file
        self.headless = headless

    def run(self):
        with sync_playwright() as playwright:
            try:
                browser = playwright.chromium.launch(headless=self.headless)
                context = browser.new_context()
                page = context.new_page()
                page.goto(self.initial_url)

                products_to_visit = []

                self.verify_page(page, "main_page", unique_page_string="E-commerce training site")
                for category in self.get_categories(page):
                    page.goto(category.url)
                    self.verify_page(page, f"category_{category.name}_page",
                                     unique_page_string=f"{category.name} category")
                    for sub_category in self.get_sub_categories(page):
                        page.goto(sub_category.url)
                        self.verify_page(page, f"sub_category_{sub_category.name}_page",
                                         unique_page_string=f"{category.name} / {sub_category.name}")
                        products_to_visit += self.get_products(page)
                        page_number = 1

                        # Paginating
                        while (next_page_btn := page.query_selector(
                                f".pagination [data-id='{page_number + 1}']")) and next_page_btn.is_enabled():
                            page_number += 1
                            logging.info(f"Navigating to page no. {page_number}")
                            page.locator(f".pagination [data-id='{page_number}']").click()
                            time.sleep(2)
                            expect(page.locator(f".pagination [data-id='{page_number}']")).to_have_class(
                                re.compile(r"active"))
                            logging.info(f"Page No. {page_number}, verified!")
                            products_to_visit += self.get_products(page)

                # Processing each product found
                for product_item in products_to_visit:
                    product_url = product_item.get("url")
                    if product_url not in self.visited:
                        page.goto(product_url)
                        self.verify_page(page, f"product_{product_item.get('name').replace(' ', '_')}_page",
                                         unique_page_string=product_item.get('name'))
                        product = self.process_product(page, category.name)
                        self.export_product(product)
                        self.visited.add(product_url)

                logging.info(f"Total Visited: {len(self.visited)}")
            except Exception as e:
                logging.error(e)

    @staticmethod
    def verify_page(page: Page, page_name: str, unique_page_string: str, product_id: str = None):
        expect(page.get_by_text(unique_page_string).first).to_be_visible()
        if product_id:
            expect(page.get_by_text(unique_page_string).first).to_be_visible()
        logging.info(f"{page_name} was verified!")

    def get_categories(self, page):
        categories = [Category(name=category_elem.text_content().strip(),
                               url=f"{self.base_url}{category_elem.get_attribute('href')}") for
                      category_elem in page.locator(".category-link").all()] or []
        logging.info(f"Categories found: {categories}")
        return categories

    def get_sub_categories(self, page):
        sub_categories = [SubCategory(name=category_elem.text_content().strip(),
                                      url=f"{self.base_url}{category_elem.get_attribute('href')}") for
                          category_elem in page.locator(".subcategory-link").all()] or []
        logging.info(f"Sub-Categories found: {sub_categories}")
        return sub_categories

    def get_products(self, page: Page):
        products = [{'name': product_elem.text_content().strip(),
                     'url': f"{self.base_url}{product_elem.get_attribute('href')}"} for product_elem in
                    page.locator(".product-wrapper a[class='title']").all()] or []
        logging.debug(f"Products found: {products}")
        return products

    @staticmethod
    def process_product(page: Page, category_name: str):
        product_elem = page.locator(".product-wrapper")
        product_id = page.url.split('/')[-1]

        product = Product(
            product_id=product_id,
            name=product_elem.locator("h4.title").text_content().strip(),
            price=product_elem.locator("h4.price").text_content().strip(),
            description=product_elem.locator("p.description").text_content().strip(),
            review_count=product_elem.locator("p.review-count").text_content().strip(),
            category=category_name
        )
        logging.debug(f"Product found: {product}")
        return product

    def export_product(self, product: Product):
        product_dict = product._asdict()
        with open(self.output_file, 'a') as file:
            file.write(json.dumps(product_dict) + '\n')


if __name__ == '__main__':
    logging.info("Running...")
    scraper = EcommerceScraper(url="https://webscraper.io/test-sites/e-commerce/ajax", output_file="products.jsonl",
                               headless=True)
    scraper.run()
    logging.info("Done!")
