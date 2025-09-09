import re
from bs4 import BeautifulSoup
import requests
import random
import logging
UNWANTED_TAGS = [
    "script", "style", "nav", "footer", "header", "aside", "form", "iframe", "noscript", "a", "button",
    "input", "img", "meta", "link", "svg", "figure", "figcaption", "video", "audio", "canvas", "path"
]

UNWANTED_CLASSNAMES = ["post_top", "tie-areas", "post_comment", "post_recommends", "post_side", "N-nav-bottom",
                        "pinglunbox"
]
logger = logging.getLogger(__name__)

def load_webpage(url: str):
    """
    Load the webpage from the url using requests + BeautifulSoup
    """
    try:
        # 更真实的浏览器 User-Agent
        user_agents = [
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
        
        headers = {
            'User-Agent': random.choice(user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        }
        
        response = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
        response.raise_for_status()
        
        # 检查是否被重定向到安全验证页面
        if "百度安全验证" in response.text or "网络不给力" in response.text:
            logger.warning(f"Detected Baidu security verification for {url}")
            return "页面内容无法获取，可能触发了安全验证"
        
        # 处理编码问题
        try:
            # 首先尝试从HTML meta标签中获取编码
            charset_match = re.search(r'charset=["\']?([^"\'>\s]+)', response.text[:1000], re.IGNORECASE)
            if charset_match:
                encoding = charset_match.group(1).lower()
                # 处理常见的编码别名
                encoding_map = {
                    'gb2312': 'gbk',
                    'gbk': 'gbk', 
                    'utf-8': 'utf-8',
                    'utf8': 'utf-8',
                    'big5': 'big5',
                    'iso-8859-1': 'utf-8'  # 通常中文网站不是这个编码
                }
                encoding = encoding_map.get(encoding, encoding)
            else:
                # 尝试从响应头获取编码
                encoding = response.encoding
                if not encoding or encoding.lower() in ['iso-8859-1', 'ascii']:
                    # 使用chardet检测编码
                    import chardet
                    detected = chardet.detect(response.content)
                    encoding = detected.get('encoding', 'utf-8')
                    confidence = detected.get('confidence', 0)
                    logger.info(f"Detected encoding: {encoding} (confidence: {confidence:.2f})")
            
            # 尝试多种编码方式
            encodings_to_try = [encoding, 'utf-8', 'gbk', 'gb2312']
            response_text = None
            
            for enc in encodings_to_try:
                try:
                    response_text = response.content.decode(enc, errors='ignore')
                    # 检查是否包含中文字符
                    if any('\u4e00' <= char <= '\u9fff' for char in response_text[:1000]):
                        logger.info(f"Successfully decoded with {enc}")
                        break
                except (UnicodeDecodeError, LookupError):
                    continue
            
            if response_text is None:
                response_text = response.content.decode('utf-8', errors='ignore')
            
            soup = BeautifulSoup(response_text, 'html.parser')
        except Exception as encoding_error:
            logger.error(f"Encoding error for {url}: {encoding_error}")
            # 如果编码检测失败，使用默认方式
            soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove unwanted tags
        for tag in UNWANTED_TAGS:
            for element in soup.find_all(tag):
                element.decompose()
        
        # Remove unwanted class names
        for classname in UNWANTED_CLASSNAMES:
            for element in soup.find_all(class_=classname):
                element.decompose()
        
        # Get clean text content
        text = soup.get_text(separator=' ', strip=True)
        
        # 清理编码问题
        try:
            # 移除控制字符和不可见字符
            text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)
            
            # 移除乱码字符（保留中文、英文、数字、基本标点）
            text = re.sub(r'[^\u4e00-\u9fff\u3400-\u4dbf\w\s\.\,\!\?\;\:\-\(\)\[\]\{\}\"\'\/\\\@\#\$\%\^\&\*\+\=\|\\\<\>\~\`]', '', text)
            
            # 移除多余的空白字符
            text = re.sub(r'\s+', ' ', text)
            # 移除多余的换行符
            text = re.sub(r'\n+', ' ', text)
            
            # 移除连续的特殊字符
            text = re.sub(r'[^\u4e00-\u9fff\w\s]{3,}', ' ', text)
            
            # 确保文本是有效的UTF-8
            text = text.encode('utf-8', errors='ignore').decode('utf-8')
            
            # 如果文本太短或包含太多乱码，返回空字符串让上层使用snippet
            chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
            total_chars = len(text)
            chinese_ratio = chinese_chars / total_chars if total_chars > 0 else 0
            logger.debug(f"Chinese chars: {chinese_chars}/{total_chars} ({chinese_ratio:.2%}) for {url}")
            if total_chars > 0 and chinese_ratio < 0.1:  # 中文字符占比小于10%
                logger.warning(f"Too few Chinese characters in content for {url}, using snippet")
                return ""  # 返回空字符串，让上层使用snippet
                
        except Exception as text_error:
            logger.error(f"Text cleaning error for {url}: {text_error}")
            # 如果清理失败，使用基本清理
            text = ' '.join(text.split())
        
        # 如果内容太短，可能没有成功获取
        if len(text) < 50:
            logger.warning(f"Content too short for {url}, length: {len(text)}")
            return ""
        
        return text
        
    except Exception as e:
        logger.error(f"Error loading webpage {url}: {e}")
        return f"页面加载失败: {str(e)}"