import os
import warnings
import time
import datetime
import urllib.parse
import json
import re
import requests
import pandas as pd
from pypdf import PdfReader
from docx import Document
import streamlit as st
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, messages_to_dict, messages_from_dict

warnings.filterwarnings("ignore")
from langgraph.prebuilt import create_react_agent

# =====================================================================
# PHẦN 1: THIẾT LẬP MÔI TRƯỜNG & GIAO DIỆN WEB
# =====================================================================
st.set_page_config(page_title="AI Agent 007", page_icon="🤖", layout="wide")
st.title("🤖 Chatbot AI Agent (Phiên Bản Tối Thượng)")
st.markdown("💡 **Siêu năng lực:** ⛅ Thời Tiết | 🕒 Thời Gian | 📈 Giá Crypto | 🔍 Wikipedia | 🧮 Máy Tính | 📄 Đọc File | 📸 Nhìn Ảnh")
st.divider()

# Xử lý API Key chống lỗi Pydantic
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY", "")

if not api_key and "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]

api_key = api_key.strip().strip("'").strip('"')

if not api_key:
    st.error("❌ **LỖI NGHIÊM TRỌNG: Streamlit Cloud chưa nhận được API Key của bạn!**")
    st.info("👉 **CÁCH KHẮC PHỤC TRÊN STREAMLIT CLOUD:**")
    st.markdown("1. Nhìn xuống góc dưới cùng bên phải của trang Web này, bấm vào chữ **`Manage app`**.")
    st.markdown("2. Bấm vào biểu tượng dấu 3 chấm (`⋮`) -> Chọn **`Settings`**.")
    st.markdown("3. Chọn mục **`Secrets`** ở menu bên trái.")
    st.markdown("4. Copy và dán chính xác dòng lệnh sau vào ô trống, sau đó bấm **Save**:")
    st.code('GOOGLE_API_KEY="DÁN_API_KEY_CỦA_BẠN_VÀO_ĐÂY (Thường bắt đầu bằng AIza... hoặc AQ...)"', language="toml")
    st.stop()

os.environ["GOOGLE_API_KEY"] = api_key

try:
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash", 
        temperature=0,
        api_key=api_key
    )
except Exception as e:
    st.error(f"❌ Lỗi khởi tạo AI: {e}")
    st.stop()

# =====================================================================
# PHẦN 2: KHO VŨ KHÍ SIÊU CẤP (7 CÔNG CỤ)
# =====================================================================
@tool
def cong_cu_thoi_tiet(dia_diem: str) -> str:
    """Tra cứu thời tiết hiện tại của một thành phố hoặc quốc gia."""
    try:
        # Sử dụng API wttr.in rất mạnh và không cần key
        res = requests.get(f"https://wttr.in/{urllib.parse.quote(dia_diem)}?format=3", timeout=5)
        return f"Thời tiết tại {dia_diem}: {res.text}"
    except Exception as e:
        return f"Lỗi: Không thể lấy dữ liệu thời tiết lúc này ({e})."

@tool
def cong_cu_thoi_gian(truy_van: str = "") -> str:
    """Tra cứu giờ giấc, ngày, tháng, năm hiện tại."""
    now = datetime.datetime.now()
    return f"Thời gian thực tế hiện tại là: {now.strftime('%H:%M:%S, ngày %d/%m/%Y')}"

@tool
def cong_cu_gia_crypto(ten_coin: str) -> str:
    """Tra cứu giá tiền điện tử (Ví dụ: BTC, ETH) bằng USD từ Binance."""
    try:
        symbol = ten_coin.upper() + "USDT"
        res = requests.get(f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}", timeout=5)
        if res.status_code == 200:
            data = res.json()
            return f"Giá hiện tại của {ten_coin.upper()} là {float(data['price']):,.2f} USD."
        return f"Không tìm thấy mã coin {ten_coin} trên sàn."
    except Exception as e:
        return f"Lỗi không thể lấy giá crypto: {e}"

@tool
def cong_cu_may_tinh(bieu_thuc: str) -> str:
    """Thực hiện các phép tính toán học."""
    try:
        return str(eval(bieu_thuc))
    except Exception as e:
        return f"Tính toán thất bại: {e}"

@tool
def cong_cu_tra_cuu_wiki(tu_khoa: str) -> str:
    """Tìm kiếm kiến thức, thông tin nhân vật, sự kiện trên mạng."""
    try:
        url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={urllib.parse.quote(tu_khoa)}&utf8=&format=json"
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5)
        data = res.json()
        if data['query']['search']:
            snippets = [re.sub('<[^<]+>', '', item['snippet']) for item in data['query']['search'][:2]]
            return f"Thông tin tìm được: {' | '.join(snippets)}"
        return "Không tìm thấy thông tin trên mạng."
    except Exception as e:
        return f"Lỗi tra cứu: {e}"

@tool
def cong_cu_doc_tai_lieu(ten_file: str) -> str:
    """Đọc nội dung văn bản từ các file .txt, .pdf, .docx, .csv có trên máy tính."""
    try:
        if not os.path.exists(ten_file):
            return f"Lỗi: Không tìm thấy file '{ten_file}'."
            
        ext = ten_file.split('.')[-1].lower()
        if ext == 'txt':
            with open(ten_file, 'r', encoding='utf-8') as f: return f.read()[:10000]
        elif ext == 'pdf':
            reader = PdfReader(ten_file)
            return "".join([page.extract_text() for page in reader.pages])[:10000]
        elif ext == 'docx':
            doc = Document(ten_file)
            return "\n".join([p.text for p in doc.paragraphs])[:10000]
        elif ext == 'csv':
            return pd.read_csv(ten_file).head(50).to_string()
        else:
            return "Định dạng file không được hỗ trợ để đọc chữ."
    except Exception as e:
        return f"Lỗi khi đọc file: {e}"

@tool
def cong_cu_luu_file(ten_file: str, noi_dung: str) -> str:
    """Lưu báo cáo, ghi chú, thư từ vào ổ cứng máy tính (.txt)."""
    try:
        with open(ten_file, 'w', encoding='utf-8') as f:
            f.write(noi_dung)
        return f"Đã lưu thành công nội dung vào file {ten_file}."
    except Exception as e:
        return f"Lỗi khi lưu file: {e}"

danh_sach_tools = [cong_cu_thoi_tiet, cong_cu_thoi_gian, cong_cu_gia_crypto, cong_cu_may_tinh, cong_cu_tra_cuu_wiki, cong_cu_doc_tai_lieu, cong_cu_luu_file]
agent = create_react_agent(llm, tools=danh_sach_tools)

# =====================================================================
# PHẦN 3: GIAO DIỆN & QUẢN LÝ LỊCH SỬ
# =====================================================================
chi_thi_he_thong = """
Bạn là siêu trợ lý AI 007 đa năng.
Quy tắc cực kỳ quan trọng:
1. Hỏi giờ/ngày/tháng -> Dùng cong_cu_thoi_gian
2. Hỏi thời tiết -> Dùng cong_cu_thoi_tiet
3. Hỏi giá coin/crypto -> Dùng cong_cu_gia_crypto
4. Hỏi kiến thức -> Dùng cong_cu_tra_cuu_wiki
5. Nếu người dùng tải file lên và nhờ đọc/tóm tắt -> Dùng cong_cu_doc_tai_lieu
"""

FILE_TRI_NHO = "chat_history.json"

def luu_tri_nho(messages):
    try:
        with open(FILE_TRI_NHO, "w", encoding="utf-8") as f:
            json.dump(messages_to_dict(messages), f, ensure_ascii=False, indent=2)
    except: pass

def tai_tri_nho():
    if os.path.exists(FILE_TRI_NHO):
        try:
            with open(FILE_TRI_NHO, "r", encoding="utf-8") as f:
                return messages_from_dict(json.load(f))
        except: pass
    return None

# --- SIDEBAR TẢI FILE LÊN ---
with st.sidebar:
    st.header("⚙️ Khu vực Tải File / Cài đặt")
    
    file_tai_len = st.file_uploader("📂 Tải tài liệu (PDF, Word, TXT, CSV) hoặc Ảnh (JPG, PNG)", 
                                    type=["txt", "pdf", "docx", "csv", "jpg", "jpeg", "png"])
    
    # Nếu người dùng tải file lên, lưu tạm vào máy chủ để Agent đọc được
    if file_tai_len:
        with open(file_tai_len.name, "wb") as f:
            f.write(file_tai_len.getbuffer())
        st.success(f"✅ Đã lưu file: **{file_tai_len.name}**")
        
        # Nếu là ảnh thì hiện preview
        if file_tai_len.name.lower().endswith(('.jpg', '.jpeg', '.png')):
            st.image(file_tai_len)
            
    st.divider()
    if st.button("🗑️ Xóa sạch trí nhớ", use_container_width=True):
        st.session_state.lich_su_chat = [SystemMessage(content=chi_thi_he_thong)]
        luu_tri_nho(st.session_state.lich_su_chat)
        st.rerun()

if "lich_su_chat" not in st.session_state:
    st.session_state.lich_su_chat = tai_tri_nho() or [SystemMessage(content=chi_thi_he_thong)]

# In lịch sử
for msg in st.session_state.lich_su_chat:
    if isinstance(msg, HumanMessage):
        with st.chat_message("user"):
            if isinstance(msg.content, list):
                st.markdown(next((item["text"] for item in msg.content if isinstance(item, dict) and item.get("type") == "text"), "[Hình ảnh đính kèm]"))
            else:
                st.markdown(msg.content)
    elif isinstance(msg, AIMessage) and msg.content:
        with st.chat_message("assistant"):
            text = "\n".join([i["text"] for i in msg.content if isinstance(i, dict) and "text" in i]) if isinstance(msg.content, list) else msg.content
            st.markdown(text)

# Khung Chat
if cau_hoi := st.chat_input("Nhập câu hỏi, tra cứu giá BTC, thời tiết, hoặc yêu cầu đọc file..."):
    with st.chat_message("user"): 
        st.markdown(cau_hoi)
    
    # Xử lý: Nếu người dùng tải ảnh lên thì đính kèm ảnh vào tin nhắn
    if file_tai_len and file_tai_len.name.lower().endswith(('.jpg', '.jpeg', '.png')):
        du_lieu_anh = file_tai_len.read()
        noi_dung_gui_ai = [
            {"type": "text", "text": cau_hoi},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{__import__('base64').b64encode(du_lieu_anh).decode('utf-8')}"}}
        ]
        tin_nhan = HumanMessage(content=noi_dung_gui_ai)
    else:
        tin_nhan = HumanMessage(content=cau_hoi)
        
    st.session_state.lich_su_chat.append(tin_nhan)
    luu_tri_nho(st.session_state.lich_su_chat)
    
    with st.chat_message("assistant"):
        with st.spinner("Agent đang vận dụng công cụ..."):
            try:
                ket_qua = agent.invoke({"messages": st.session_state.lich_su_chat})
                st.session_state.lich_su_chat = ket_qua["messages"]
                luu_tri_nho(st.session_state.lich_su_chat)
                
                final_content = st.session_state.lich_su_chat[-1].content
                st.markdown("\n".join([i["text"] for i in final_content if isinstance(i, dict)]) if isinstance(final_content, list) else final_content)
            except Exception as e:
                error_msg = str(e)
                if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                    st.error("⏳ CẢNH BÁO: Chạm giới hạn API. Vui lòng đợi 1 phút!")
                else:
                    st.error(f"❌ LỖI: {e}")
                st.session_state.lich_su_chat.pop()