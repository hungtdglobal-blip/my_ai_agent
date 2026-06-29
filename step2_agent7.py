import os
import warnings
import time
import datetime
import urllib.request
import urllib.parse
import json
import re
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
st.set_page_config(page_title="AI Agent 007", page_icon="🤖", layout="centered")
st.title("🤖 Chatbot AI Agent (Bản Web)")
st.markdown("💡 **Siêu năng lực:** Nhìn ảnh (MỚI) | Tra cứu mạng | Tính toán | File | 🧠 **Trí nhớ**")
st.divider()

# --- CƠ CHẾ SỬA LỖI PYDANTIC VALIDATION ERROR ---
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY", "")

if not api_key and "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]

api_key = api_key.strip().strip("'").strip('"')

if not api_key:
    st.error("❌ **LỖI NGHIÊM TRỌNG: Streamlit Cloud chưa nhận được API Key của bạn!**")
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
# PHẦN 2: KHO VŨ KHÍ THỰC TẾ (TOOLS) CHO AGENT
# =====================================================================
@tool
def cong_cu_may_tinh(bieu_thuc: str) -> str:
    """Hữu ích khi bạn cần thực hiện các phép tính toán học."""
    try:
        time.sleep(1)
        return str(eval(bieu_thuc))
    except Exception as e:
        return f"Tính toán thất bại: {e}"

@tool
def cong_cu_thoi_gian(truy_van: str = "") -> str:
    """Dùng công cụ này khi người dùng hỏi về giờ giấc, ngày, tháng, năm hiện tại."""
    now = datetime.datetime.now()
    thoi_gian_hien_tai = now.strftime("%H:%M:%S, ngày %d/%m/%Y")
    time.sleep(1)
    return f"Thời gian thực tế hiện tại: {thoi_gian_hien_tai}"

@tool
def cong_cu_tra_cuu_wiki(tu_khoa: str) -> str:
    """Dùng để tìm kiếm kiến thức, thông tin nhân vật, sự kiện trên mạng."""
    try:
        time.sleep(1)
        url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={urllib.parse.quote(tu_khoa)}&utf8=&format=json"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))
            if data['query']['search']:
                snippets = [re.sub('<[^<]+>', '', item['snippet']) for item in data['query']['search'][:2]]
                return f"Thông tin tìm được: {' | '.join(snippets)}"
            return "Không tìm thấy thông tin trên mạng."
    except Exception as e:
        return f"Lỗi tra cứu: {e}"

@tool
def cong_cu_luu_file(ten_file: str, noi_dung: str) -> str:
    """Dùng để lưu báo cáo, ghi chú, thư từ vào ổ cứng máy tính."""
    try:
        time.sleep(1)
        with open(ten_file, 'w', encoding='utf-8') as f:
            f.write(noi_dung)
        return f"Đã lưu thành công nội dung vào file {ten_file}."
    except Exception as e:
        return f"Lỗi khi lưu file: {e}"

@tool
def cong_cu_doc_file(ten_file: str) -> str:
    """Dùng để đọc nội dung từ file có sẵn trên máy tính."""
    try:
        time.sleep(1)
        if not os.path.exists(ten_file):
            return f"Lỗi: Không tìm thấy file '{ten_file}' trên máy tính."
        with open(ten_file, 'r', encoding='utf-8') as f:
            noi_dung = f.read()
        return f"Nội dung file '{ten_file}':\n{noi_dung[:10000]}"
    except Exception as e:
        return f"Lỗi khi đọc file: {e}"

@tool
def cong_cu_gia_crypto(ten_coin: str) -> str:
    """Tra cứu giá tiền điện tử theo thời gian thực từ sàn Binance."""
    try:
        time.sleep(1)
        symbol = ten_coin.upper() + "USDT"
        url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))
            return f"Giá hiện tại của {ten_coin.upper()} đang là {float(data['price']):,.2f} USD."
    except Exception as e:
        return f"Lỗi không thể lấy giá crypto: {e}"

danh_sach_tools = [cong_cu_may_tinh, cong_cu_thoi_gian, cong_cu_tra_cuu_wiki, cong_cu_luu_file, cong_cu_doc_file, cong_cu_gia_crypto]

# =====================================================================
# PHẦN 3: ĐÀO TẠO AGENT
# =====================================================================
agent = create_react_agent(llm, tools=danh_sach_tools)

# =====================================================================
# PHẦN 4: GIAO DIỆN CHAT VÀ QUẢN LÝ LỊCH SỬ
# =====================================================================
chi_thi_he_thong = "Bạn là trợ lý ảo siêu việt có khả năng nhìn ảnh và dùng công cụ. Trả lời lịch sự bằng Markdown."
FILE_TRI_NHO = "chat_history.json"

def luu_tri_nho(messages):
    try:
        with open(FILE_TRI_NHO, "w", encoding="utf-8") as f:
            json.dump(messages_to_dict(messages), f, ensure_ascii=False, indent=2)
    except:
        pass

def tai_tri_nho():
    if os.path.exists(FILE_TRI_NHO):
        try:
            with open(FILE_TRI_NHO, "r", encoding="utf-8") as f:
                return messages_from_dict(json.load(f))
        except:
            pass
    return None

# --- THANH CÀI ĐẶT BÊN TRÁI & Ô UPLOAD ẢNH ---
with st.sidebar:
    st.header("⚙️ Cấu hình Hệ thống")
    
    # Nâng cấp: Cho phép tải ảnh lên trực tiếp từ Sidebar
    file_anh_tai_len = st.file_uploader("📸 Tải ảnh lên để AI phân tích", type=["jpg", "jpeg", "png"])
    if file_anh_tai_len:
        st.image(file_anh_tai_len, caption="Ảnh bạn vừa tải lên", use_container_width=True)
        
    st.divider()
    if st.button("🗑️ Xóa sạch trí nhớ", use_container_width=True):
        st.session_state.lich_su_chat = [SystemMessage(content=chi_thi_he_thong)]
        luu_tri_nho(st.session_state.lich_su_chat)
        st.rerun()

if "lich_su_chat" not in st.session_state:
    st.session_state.lich_su_chat = tai_tri_nho() or [SystemMessage(content=chi_thi_he_thong)]

# Hiển thị hội thoại cũ
for msg in st.session_state.lich_su_chat:
    if isinstance(msg, HumanMessage):
        with st.chat_message("user"):
            # Nếu nội dung tin nhắn cũ dạng list (chứa cả ảnh), chỉ hiển thị phần text để giao diện gọn gàng
            if isinstance(msg.content, list):
                text_content = next((item["text"] for item in msg.content if isinstance(item, dict) and item.get("type") == "text"), "[Yêu cầu kèm hình ảnh]")
                st.markdown(text_content)
            else:
                st.markdown(msg.content)
    elif isinstance(msg, AIMessage) and msg.content:
        with st.chat_message("assistant"):
            text = "\n".join([i["text"] for i in msg.content if isinstance(i, dict) and "text" in i]) if isinstance(msg.content, list) else msg.content
            st.markdown(text)

# --- Ô NHẬP LIỆU Ở ĐÁY MÀN HÌNH ---
if cau_hoi := st.chat_input("Nhập câu hỏi hoặc yêu cầu phân tích ảnh tại đây..."):
    with st.chat_message("user"): 
        st.markdown(cau_hoi)
    
    # XỬ LÝ ĐA PHƯƠNG TIỆN: Nếu người dùng có upload ảnh
    if file_anh_tai_len:
        # Đọc dữ liệu binary của ảnh và chuyển sang cấu trúc Multimodal của LangChain
        du_lieu_anh = file_anh_tai_len.read()
        noi_dung_gui_ai = [
            {"type": "text", "text": cau_hoi},
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{st.image_to_base64(file_anh_tai_len) if hasattr(st, 'image_to_base64') else __import__('base64').b64encode(du_lieu_anh).decode('utf-8')}"}
            }
        ]
        tin_nhan_nguoi_dung = HumanMessage(content=noi_dung_gui_ai)
    else:
        tin_nhan_nguoi_dung = HumanMessage(content=cau_hoi)
        
    st.session_state.lich_su_chat.append(tin_nhan_nguoi_dung)
    luu_tri_nho(st.session_state.lich_su_chat)
    
    with st.chat_message("assistant"):
        with st.spinner("Agent đang quan sát ảnh và xử lý..."):
            try:
                ket_qua = agent.invoke({"messages": st.session_state.lich_su_chat})
                st.session_state.lich_su_chat = ket_qua["messages"]
                luu_tri_nho(st.session_state.lich_su_chat)
                
                final_content = st.session_state.lich_su_chat[-1].content
                if isinstance(final_content, list):
                    text_output = "\n".join([i["text"] for i in final_content if isinstance(i, dict) and "text" in i])
                    st.markdown(text_output)
                else:
                    st.markdown(final_content)
            except Exception as e:
                error_msg = str(e)
                if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                    st.error("⏳ **CẢNH BÁO:** Chạm giới hạn API. Vui lòng đợi 1 phút!")
                else:
                    st.error(f"❌ **LỖI:** {e}")
                st.session_state.lich_su_chat.pop()