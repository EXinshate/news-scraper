# 版权声明
# Copyright © 2024 周政. All rights reserved.
# 本代码仅供学习和研究使用，未经作者许可不得用于商业用途。
# 有开发需求请邮箱联系: 758285009@qq.com
# 外文网站运行较慢，全局使用科学上网工具性能会更加优异
import requests
from bs4 import BeautifulSoup
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

# 定义常量
NEWS_URL_CONSTANT = "https://www.artnews.com/c/art-news/market/"
NEWS_URL_1 = "https://www.artnews.com/art-news/market/"
START_PAGE = 2
END_PAGE = 100  # 根据需要调整结束页码

def fetch_html(url, max_retries=3, retry_delay=2):
    """获取网页的HTML源代码，带有重试机制。

    Args:
        url (str): 网页的URL。
        max_retries (int): 最大重试次数。
        retry_delay (int): 重试之间的延迟秒数。

    Returns:
        str: 如果请求成功则返回网页的HTML文本；如果失败则返回None。
    """
    for attempt in range(max_retries):
        try:
            response = requests.get(url)
            response.raise_for_status()  # 对于不成功的HTTP响应抛出异常
            return response.text
        except requests.exceptions.RequestException as e:
            print(f"尝试获取URL {url} 的内容失败 (尝试 {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)  # 等待后重试

    print(f"无法获取URL {url} 的内容，已达到最大重试次数。")
    return None

def parse_news(html):
    """解析HTML内容并提取特定的新闻标题和链接。

    Args:
        html (str): 网页的HTML文本。

    Returns:
        list: 包含新闻标题和链接的元组列表。
    """
    news_list = []
    try:
        soup = BeautifulSoup(html, 'html.parser')
        # 使用更宽松的选择器来匹配目标<h3>标签
        for item in soup.select('h3.c-title'):
            a_tag = item.find('a', class_='c-title__link')
            if a_tag and 'href' in a_tag.attrs:
                title = a_tag.get_text(strip=True)  # 获取并清理标题文本
                link = a_tag['href']  # 获取链接
                news_list.append((title, link))
        return news_list
    except Exception as e:
        print(f"解析HTML时出错: {e}")
        return []

def filter_news_by_keyword(news_list, keyword=None):
    """根据关键词过滤新闻列表，忽略大小写。

    Args:
        news_list (list): 包含新闻标题和链接的元组列表。
        keyword (str, optional): 用于过滤的关键词，默认为None。

    Returns:
        list: 根据关键词过滤后的新闻列表。
    """
    if not keyword:  # 如果没有提供关键词，则返回原始列表
        return news_list
    keyword_lower = keyword.lower()
    filtered_news = [news for news in news_list if keyword_lower in news[0].lower()]
    return filtered_news

def display_news(news_list):
    """以格式化的方式显示新闻列表。

    Args:
        news_list (list): 包含新闻标题和链接的元组列表。
    """
    if not news_list:
        print("没有找到符合您标准的新闻。")
        return

    print("--------------------")
    for i, (title, link) in enumerate(news_list, 1):
        print(f"{i}. {title}")  # 显示序号和新闻标题
        print(f"   链接: {link}")  # 显示新闻链接
        print("--------------------")

def get_user_input():
    """获取用户输入的关键词。

    Returns:
        str: 用户输入的关键词，如果取消对话框则返回None。
    """
    keyword = input("请输入涉及标题的关键词（直接按Enter键跳过）：") or None
    return keyword

def fetch_and_parse_page(page, base_url):
    url = base_url if page == 1 else f"{base_url}page/{page}/"
    html = fetch_html(url)
    if html:
        return parse_news(html)
    return []

def main():
    """程序的主要逻辑，负责调用其他函数完成抓取、解析、过滤和显示新闻的过程。"""
    keyword = get_user_input()  # 获取用户输入的关键词

    all_news = []

    urls_to_fetch = [
        (page, NEWS_URL_CONSTANT) for page in range(START_PAGE, END_PAGE + 1)
    ] + [
        (page, NEWS_URL_1) for page in range(START_PAGE, END_PAGE + 1)
    ]

    total_pages = len(urls_to_fetch)
    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_url = {
            executor.submit(fetch_and_parse_page, page, base_url): (page, base_url)
            for page, base_url in urls_to_fetch
        }

        with tqdm(total=total_pages, desc="Fetching pages", unit="page") as pbar:
            for future in as_completed(future_to_url):
                page, base_url = future_to_url[future]
                try:
                    news_list = future.result()
                    all_news.extend(news_list)
                except Exception as exc:
                    print(f'{page} 页面抓取生成异常: {exc}')
                finally:
                    pbar.update(1)

    # 过滤并显示新闻
    if all_news:
        filtered_news = filter_news_by_keyword(all_news, keyword)
        display_news(filtered_news)
    else:
        print("未找到任何新闻文章。")

if __name__ == "__main__":
    main()