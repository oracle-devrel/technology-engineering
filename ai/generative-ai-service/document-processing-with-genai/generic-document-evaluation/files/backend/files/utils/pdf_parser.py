import PyPDF2
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer, LTChar, LTFigure
import pdfplumber
from PIL import Image
from pdf2image import convert_from_path
import pytesseract
import os
from langchain.docstore.document import Document
from langchain.vectorstores import Qdrant
from langchain_community.embeddings import OCIGenAIEmbeddings
import oci

class PDFParser:
    def __init__(self, compartment_id):
        self.compartment_id = compartment_id
        self.CONFIG_PROFILE = "DEFAULT"
        self.config = oci.config.from_file('~/.oci/config', self.CONFIG_PROFILE)
    
    def is_bold(self, font_name):
        bold_indicators = ['bold', 'Black', 'Heavy']
        return any(indicator.lower() in font_name.lower() for indicator in bold_indicators if isinstance(font_name, str))

    def extract_bold_sentences(self, page_text, line_formats):
        bold_sentences = []
        for line, formats in zip(page_text, line_formats):
            if any(self.is_bold(font) for font in formats):
                bold_sentences.append(line.strip())
        return ', '.join(bold_sentences)

    def text_extraction(self, element):
        line_text = element.get_text()
        line_formats = []
        for text_line in element:
            if isinstance(text_line, LTTextContainer):
                for character in text_line:
                    if isinstance(character, LTChar):
                        line_formats.append(character.fontname)
        format_per_line = list(set(line_formats))
        return (line_text, format_per_line)

    def extract_table(self, pdf_path, page_num, table_num):
        with pdfplumber.open(pdf_path) as pdf:
            page = pdf.pages[page_num]
            table = page.extract_tables()[table_num]
        return table

    def fill_missing_values(self, table):
        filled_table = []
        prev_row = None
        
        for row in table:
            filled_row = []
            for idx, cell in enumerate(row):
                if cell is None or cell.strip() == '':
                    if prev_row and len(prev_row) > idx:
                        filled_row.append(prev_row[idx])
                    else:
                        filled_row.append('None')
                else:
                    filled_row.append(cell)
            filled_table.append(filled_row)
            prev_row = filled_row
        
        return filled_table

    def table_converter(self, table):
        table = self.fill_missing_values(table)
        table_string = ''
        for row in table:
            cleaned_row = [item.replace('\n', ' ') if item is not None else 'None' for item in row]
            table_string += ('|' + '|'.join(cleaned_row) + '|\n')
        return table_string.strip()

    def is_element_inside_any_table(self, element, page, tables):
        x0, y0up, x1, y1up = element.bbox
        y0 = page.bbox[3] - y1up
        y1 = page.bbox[3] - y0up
        for table in tables:
            tx0, ty0, tx1, ty1 = table.bbox
            if tx0 <= x0 <= x1 <= tx1 and ty0 <= y0 <= y1:
                return True
        return False

    def find_table_for_element(self, element, page, tables):
        x0, y0up, x1, y1up = element.bbox
        y0 = page.bbox[3] - y1up
        y1 = page.bbox[3] - y0up
        for i, table in enumerate(tables):
            tx0, ty0, tx1, ty1 = table.bbox
            if tx0 <= x0 <= x1 and ty0 <= y0 <= y1:
                return i
        return None

    def crop_image(self, element, pageObj):
        [image_left, image_top, image_right, image_bottom] = [element.x0, element.y0, element.x1, element.y1]
        pageObj.mediabox.lower_left = (image_left, image_bottom)
        pageObj.mediabox.upper_right = (image_right, image_top)
        cropped_pdf_writer = PyPDF2.PdfWriter()
        cropped_pdf_writer.add_page(pageObj)
        with open('cropped_image.pdf', 'wb') as cropped_pdf_file:
            cropped_pdf_writer.write(cropped_pdf_file)

    def convert_to_images(self, input_file):
        images = convert_from_path(input_file)
        image = images[0]
        output_file = 'PDF_image.png'
        image.save(output_file, 'PNG')

    def image_to_text(self, image_path):
        img = Image.open(image_path)
        text = pytesseract.image_to_string(img)
        return text

    def parse_pdf(self, pdf_path):
        pdfFileObj = open(pdf_path, 'rb')
        pdfReader = PyPDF2.PdfReader(pdfFileObj)
        text_per_page = {}
        image_flag = False

        for pagenum, page in enumerate(extract_pages(pdf_path)):
            pageObj = pdfReader.pages[pagenum]
            page_text = []
            line_format = []
            text_from_images = []
            text_from_tables = []
            page_content = []
            table_in_page = -1
            pdf = pdfplumber.open(pdf_path)
            page_tables = pdf.pages[pagenum]
            tables = page_tables.find_tables()
            if tables:
                table_in_page = 0

            for table_num in range(len(tables)):
                table = self.extract_table(pdf_path, pagenum, table_num)
                table_string = self.table_converter(table)
                text_from_tables.append(table_string)

            page_elements = [(element.y1, element) for element in page._objs]
            page_elements.sort(key=lambda a: a[0], reverse=True)

            for component in page_elements:
                element = component[1]

                if table_in_page != -1 and self.is_element_inside_any_table(element, page, tables):
                    table_found = self.find_table_for_element(element, page, tables)
                    if table_found == table_in_page and table_found is not None:
                        page_content.append(text_from_tables[table_in_page])
                        page_text.append('table')
                        line_format.append('table')
                        table_in_page += 1
                    continue

                if isinstance(element, LTTextContainer):
                    (line_text, format_per_line) = self.text_extraction(element)
                    page_text.append(line_text)
                    line_format.append(format_per_line)
                    page_content.append(line_text)

                if isinstance(element, LTFigure):
                    self.crop_image(element, pageObj)
                    self.convert_to_images('cropped_image.pdf')
                    image_text = self.image_to_text('PDF_image.png')
                    text_from_images.append(image_text)
                    page_content.append(image_text)
                    page_text.append('image')
                    line_format.append('image')
                    image_flag = True

            dctkey = 'Page_' + str(pagenum)
            text_per_page[dctkey] = [page_text, line_format, text_from_images, text_from_tables, page_content]

        pdfFileObj.close()
        if image_flag:
            os.remove('cropped_image.pdf')
            os.remove('PDF_image.png')

        docs = []
        for page_key, page_data in text_per_page.items():
            page_text = page_data[0]
            line_formats = page_data[1]
            page_content = page_data[4]
            page_content_string = ''.join(page_content)
            topics = self.extract_bold_sentences(page_text, line_formats)
            doc = Document(
                page_content=page_content_string,
                metadata={"source": pdf_path, "page": page_key[5:], "topics": topics}
            )
            docs.append(doc)

        return docs

    def create_embeddings(self, docs):
        embeddings = OCIGenAIEmbeddings(
            model_id="cohere.embed-multilingual-v3.0",
            service_endpoint="https://inference.generativeai.us-chicago-1.oci.oraclecloud.com",
            compartment_id=self.compartment_id,
        )
        url = "http://138.2.160.167:6333"
        db = Qdrant.from_documents(
            docs,
            embeddings,
            url=url,
            prefer_grpc=False,
            collection_name="harsh_data"
        )
        return db
