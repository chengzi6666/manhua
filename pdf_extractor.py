import os
import logging
import time

logger = logging.getLogger(__name__)

RAPIDOCRPDF_AVAILABLE = False
PDF_OXIDE_AVAILABLE = False

try:
    from rapidocr_pdf import RapidOCRPDF
    RAPIDOCRPDF_AVAILABLE = True
    logger.info("✅ RapidOCRPDF已安装")
except ImportError:
    logger.warning("❌ RapidOCRPDF未安装")

try:
    from pdf_oxide import PdfDocument
    PDF_OXIDE_AVAILABLE = True
    logger.info("✅ pdf_oxide已安装")
except ImportError:
    logger.warning("❌ pdf_oxide未安装")

rapidocr_pdf_instance = None

def get_rapidocr_pdf_instance():
    global rapidocr_pdf_instance
    if rapidocr_pdf_instance is None and RAPIDOCRPDF_AVAILABLE:
        try:
            rapidocr_pdf_instance = RapidOCRPDF()
            logger.info("✅ RapidOCRPDF实例初始化成功")
        except Exception as e:
            logger.error(f"❌ RapidOCRPDF初始化失败: {str(e)}")
            rapidocr_pdf_instance = None
    return rapidocr_pdf_instance

def is_scanned_pdf(pdf_path):
    """快速判断PDF是否为扫描版（图片版）"""
    try:
        import fitz
        doc = fitz.open(pdf_path)
        
        text_chars = 0
        image_count = 0
        
        for page in doc[:3]:
            text = page.get_text("text")
            text_chars += len(text.strip())
            
            images = page.get_images(full=True)
            image_count += len(images)
        
        doc.close()
        
        if text_chars < 50 and image_count > 0:
            logger.info(f"检测到扫描版PDF: 文本{text_chars}字符, 图片{image_count}个")
            return True
        
        return False
    except Exception as e:
        logger.warning(f"PDF类型检测失败: {str(e)}")
        return False

def extract_text_with_mineru_style(pdf_path):
    start_time = time.time()
    
    try:
        is_scanned = is_scanned_pdf(pdf_path)
        
        if is_scanned:
            logger.info("检测到扫描版PDF，使用RapidOCRPDF进行OCR识别...")
            text = extract_text_with_rapidocr_pdf(pdf_path, force_ocr=True)
            
            if text and len(text.strip()) > 20:
                elapsed = time.time() - start_time
                logger.info(f"✅ RapidOCRPDF OCR识别成功，耗时{elapsed:.2f}秒")
                return text
            
            logger.info("RapidOCRPDF OCR失败，尝试备用OCR方法...")
            ocr_text = extract_text_from_scanned_pdf(pdf_path)
            
            if ocr_text and len(ocr_text.strip()) > 20:
                elapsed = time.time() - start_time
                logger.info(f"✅ 备用OCR识别成功，耗时{elapsed:.2f}秒")
                return ocr_text
            
            return None
        
        logger.info("文字版PDF，使用pdf_oxide快速提取...")
        text = extract_text_with_pdf_oxide(pdf_path)
        
        if text and len(text.strip()) > 20:
            elapsed = time.time() - start_time
            logger.info(f"✅ pdf_oxide提取成功，耗时{elapsed:.2f}秒")
            return text
        
        logger.info("pdf_oxide提取失败，尝试PyMuPDF...")
        text = extract_with_pymupdf(pdf_path)
        
        if text and len(text.strip()) > 20:
            elapsed = time.time() - start_time
            logger.info(f"✅ PyMuPDF提取成功，耗时{elapsed:.2f}秒")
            return text
        
        logger.info("PyMuPDF也失败，尝试RapidOCRPDF...")
        text = extract_text_with_rapidocr_pdf(pdf_path, force_ocr=False)
        
        if text and len(text.strip()) > 20:
            elapsed = time.time() - start_time
            logger.info(f"✅ RapidOCRPDF提取成功，耗时{elapsed:.2f}秒")
            return text
        
        logger.info("所有文字提取均失败，尝试OCR识别...")
        ocr_text = extract_text_from_scanned_pdf(pdf_path)
        
        if ocr_text and len(ocr_text.strip()) > 20:
            elapsed = time.time() - start_time
            logger.info(f"✅ OCR识别成功，耗时{elapsed:.2f}秒")
            return ocr_text
        
        return None
    except Exception as e:
        logger.error(f"MinerU风格提取失败: {str(e)}")
        return None

def extract_text_with_rapidocr_pdf(pdf_path, force_ocr=False):
    if not RAPIDOCRPDF_AVAILABLE:
        return None
    
    try:
        pdf_extracter = get_rapidocr_pdf_instance()
        if pdf_extracter is None:
            return None
        
        results = pdf_extracter(pdf_path, force_ocr=force_ocr)
        
        if not results:
            return None
        
        all_texts = []
        for page_num, page_text, confidence in results:
            if page_text and len(page_text.strip()) > 5:
                all_texts.append(page_text)
        
        if all_texts:
            return '\n\n'.join(all_texts)
        
        return None
    except Exception as e:
        logger.error(f"RapidOCRPDF提取失败: {str(e)}")
        return None

def extract_text_with_pdf_oxide(pdf_path):
    if not PDF_OXIDE_AVAILABLE:
        return None
    
    try:
        doc = PdfDocument(pdf_path)
        all_texts = []
        for page_idx in range(len(doc)):
            text = doc.extract_text(page_idx)
            if text and len(text.strip()) > 5:
                all_texts.append(text)
        
        if all_texts:
            return '\n\n'.join(all_texts)
        
        return None
    except Exception as e:
        logger.error(f"pdf_oxide提取失败: {str(e)}")
        return None

def extract_text_from_pdf_combined(pdf_path):
    text = ""
    all_texts = []
    
    try:
        text = extract_with_pdfminer(pdf_path)
        if text and len(text.strip()) > 30:
            logger.info(f"pdfminer.six成功提取文本，共{len(text)}字符")
            return text
        elif text:
            all_texts.append(text)
    except Exception as e:
        logger.warning(f"pdfminer.six提取失败: {str(e)}")
    
    try:
        text = extract_with_pypdfium2(pdf_path)
        if text and len(text.strip()) > 30:
            logger.info(f"pypdfium2成功提取文本，共{len(text)}字符")
            return text
        elif text:
            all_texts.append(text)
    except Exception as e:
        logger.warning(f"pypdfium2提取失败: {str(e)}")
    
    try:
        text = extract_with_pypdf2(pdf_path)
        if text and len(text.strip()) > 30:
            logger.info(f"PyPDF2成功提取文本，共{len(text)}字符")
            return text
        elif text:
            all_texts.append(text)
    except Exception as e:
        logger.warning(f"PyPDF2提取失败: {str(e)}")
    
    try:
        text = extract_with_pymupdf(pdf_path)
        if text and len(text.strip()) > 30:
            logger.info(f"PyMuPDF成功提取文本，共{len(text)}字符")
            return text
        elif text:
            all_texts.append(text)
    except Exception as e:
        logger.warning(f"PyMuPDF提取失败: {str(e)}")
    
    if all_texts:
        combined = '\n'.join(all_texts)
        if len(combined.strip()) > 20:
            logger.info(f"综合提取成功，共{len(combined)}字符")
            return combined
    
    return text

def extract_with_pdfminer(pdf_path):
    try:
        from pdfminer.high_level import extract_text
        
        text = extract_text(pdf_path)
        
        if text:
            lines = text.split('\n')
            cleaned_lines = []
            for line in lines:
                line = line.strip()
                if line and len(line) > 1:
                    cleaned_lines.append(line)
            return '\n'.join(cleaned_lines)
        
        return ""
    except ImportError:
        logger.warning("pdfminer.six未安装")
        return ""
    except Exception as e:
        logger.error(f"pdfminer.six提取失败: {str(e)}")
        return ""

def extract_with_pypdfium2(pdf_path):
    try:
        import pypdfium2 as pdfium
        
        pdf = pdfium.PdfDocument(pdf_path)
        text = ""
        
        for i in range(len(pdf)):
            page = pdf[i]
            page_text = page.get_textpage().get_text_range()
            if page_text:
                text += page_text + "\n"
        
        if text:
            lines = text.split('\n')
            cleaned_lines = []
            for line in lines:
                line = line.strip()
                if line and len(line) > 1:
                    cleaned_lines.append(line)
            return '\n'.join(cleaned_lines)
        
        return ""
    except ImportError:
        logger.warning("pypdfium2未安装")
        return ""
    except Exception as e:
        logger.error(f"pypdfium2提取失败: {str(e)}")
        return ""

def extract_with_pypdf2(pdf_path):
    try:
        from PyPDF2 import PdfReader
        
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        
        if text:
            lines = text.split('\n')
            cleaned_lines = []
            for line in lines:
                line = line.strip()
                if line and len(line) > 1:
                    cleaned_lines.append(line)
            return '\n'.join(cleaned_lines)
        
        return ""
    except ImportError:
        return ""

def extract_with_pymupdf(pdf_path):
    try:
        import fitz
        
        doc = fitz.open(pdf_path)
        text = ""
        
        for page in doc:
            page_text = page.get_text("text")
            if page_text:
                text += page_text + "\n"
        
        if text:
            lines = text.split('\n')
            cleaned_lines = []
            for line in lines:
                line = line.strip()
                if line and len(line) > 1:
                    cleaned_lines.append(line)
            return '\n'.join(cleaned_lines)
        
        return ""
    except ImportError:
        return ""

def extract_text_from_scanned_pdf(pdf_path):
    try:
        import pypdfium2 as pdfium
        from PIL import Image, ImageEnhance, ImageFilter
        
        pdf = pdfium.PdfDocument(pdf_path)
        text = ""
        total_pages = len(pdf)
        
        available_ocr_tools = []
        try:
            import easyocr
            available_ocr_tools.append('easyocr')
        except ImportError:
            pass
        try:
            import pytesseract
            pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
            
            if os.path.exists(r'C:\Users\matiancheng\Downloads\chi_sim.traineddata'):
                os.environ['TESSDATA_PREFIX'] = r'C:\Users\matiancheng\Downloads'
            elif os.path.exists(r'C:\Program Files\Tesseract-OCR\tessdata\chi_sim.traineddata'):
                os.environ['TESSDATA_PREFIX'] = r'C:\Program Files\Tesseract-OCR\tessdata'
            
            available_ocr_tools.append('tesseract')
        except ImportError:
            pass
        
        if not available_ocr_tools:
            logger.warning("没有可用的OCR工具")
            return None
        
        max_pages = min(total_pages, 10)
        logger.info(f"扫描版PDF共{total_pages}页，识别前{max_pages}页...")
        
        reader = None
        if 'easyocr' in available_ocr_tools:
            try:
                reader = easyocr.Reader(['ch_sim', 'en'], gpu=False)
                logger.info("EasyOCR加载成功")
            except Exception as e:
                logger.error(f"EasyOCR加载失败: {str(e)}")
                reader = None
        
        for i in range(max_pages):
            page = pdf[i]
            pil_image = page.render(scale=2).to_pil()
            
            gray = pil_image.convert('L')
            pixels = gray.getdata()
            avg_brightness = sum(pixels) / len(pixels)
            if avg_brightness > 240:
                logger.info(f"第{i+1}页为空白页，跳过")
                continue
            
            try:
                enhanced = enhance_image_for_ocr(gray)
                
                if reader and 'easyocr' in available_ocr_tools:
                    try:
                        results = reader.readtext(pil_image)
                        page_text = '\n'.join([item[1] for item in results])
                        if page_text and len(page_text.strip()) > 5:
                            text += f"--- 第{i+1}页 ---\n{page_text}\n\n"
                            logger.info(f"第{i+1}页识别成功(EasyOCR)，{len(page_text.strip())}字符")
                        else:
                            logger.info(f"第{i+1}页识别内容过少，跳过")
                    except Exception as e:
                        logger.error(f"EasyOCR识别第{i+1}页失败: {str(e)}")
                
                elif 'tesseract' in available_ocr_tools:
                    try:
                        page_text = pytesseract.image_to_string(pil_image, lang='chi_sim+eng',
                            config='--psm 3 --oem 3')
                        if page_text and len(page_text.strip()) > 5:
                            text += f"--- 第{i+1}页 ---\n{page_text}\n\n"
                            logger.info(f"第{i+1}页识别成功(Tesseract)，{len(page_text.strip())}字符")
                        else:
                            logger.info(f"第{i+1}页识别内容过少，跳过")
                    except Exception as e:
                        logger.error(f"Tesseract识别第{i+1}页失败: {str(e)}")
            except Exception as e:
                logger.error(f"第{i+1}页图像处理失败: {str(e)}")
        
        return text.strip() if text else None
    except Exception as e:
        logger.error(f"扫描版PDF处理失败: {str(e)}")
        return None

def enhance_image_for_ocr(image):
    from PIL import ImageEnhance, ImageFilter
    
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(1.5)
    
    enhancer = ImageEnhance.Brightness(image)
    image = enhancer.enhance(1.1)
    
    image = image.filter(ImageFilter.MedianFilter(size=3))
    
    image = image.point(lambda x: 0 if x < 128 else 255, '1')
    
    return image