from Tools import LeclercProductsFetcher
from Tools import LeclercProductsAnalyser


def demo_leclerc_fetcher():
    LeclercProductsFetcher.run(html_path="assets/scrapped.html")
    LeclercProductsFetcher.run(html_path="assets/scrapped1.html")
    LeclercProductsAnalyser.run(json_path="assets/products.json")


if __name__ == "__main__":
    demo_leclerc_fetcher()
