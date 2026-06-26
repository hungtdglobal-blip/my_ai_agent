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
st.markdown("💡 **Siêu năng lực:** Tra cứu mạng | Tính toán | File | 🧠 **Trí nhớ** | 📈 **Giá Crypto (MỚI)**")
st.divider()

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY", "").strip().strip("'").strip('"')
os.environ["GOOGLE_API_KEY"] = api_key

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash", 
    temperature=0
)

# =====================================================================
# PHẦN 2: KHO VŨ KHÍ THỰC TẾ (TOOLS) CHO AGENT
# =====================================================================

@tool
def cong_cu_may_tinh(bieu_thuc: str) -> str:
    """Hữu ích khi bạn cần thực hiện các phép tính toán học (Cộng, trừ, nhân, chia)."""
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
                snippets = []
                for item in data['query']['search'][:2]:
                    snippet_clean = re.sub('<[^<]+>', '', item['snippet'])
                    snippets.append(snippet_clean)
                ket_qua_gop = " | ".join(snippets)
                return f"Thông tin tìm được: {ket_qua_gop}"
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
        if len(noi_dung) > 10000:
            noi_dung = noi_dung[:10000] + "\n\n... [Cắt bớt do quá dài] ..."
        return f"Nội dung file '{ten_file}':\n{noi_dung}"
    except Exception as e:
        return f"Lỗi khi đọc file: {e}"

# --- CÔNG CỤ MỚI: TÍCH HỢP API THẾ GIỚI THỰC ---
@tool
def cong_cu_gia_crypto(ten_coin: str) -> str:
    """
    Dùng để tra cứu giá tiền điện tử (Bitcoin, Ethereum...) theo thời gian thực từ sàn Binance.
    Đầu vào là mã coin viết tắt (Ví dụ: 'BTC', 'ETH', 'BNB', 'SOL').
    """
    try:
        time.sleep(1)
        # Sàn Binance yêu cầu mã cặp giao dịch, vd: BTCUSDT
        symbol = ten_coin.upper() + "USDT"
        url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))
            gia_usd = float(data['price'])
            return f"Giá hiện tại của {ten_coin.upper()} đang là {gia_usd:,.2f} USD."
    except urllib.error.HTTPError as e:
        return f"Lỗi: Không tìm thấy mã coin '{ten_coin}' hoặc mã không hợp lệ."
    except Exception as e:
        return f"Lỗi không thể lấy giá crypto: {e}"

# Đăng ký vũ khí mới
danh_sach_tools = [cong_cu_may_tinh, cong_cu_thoi_gian, cong_cu_tra_cuu_wiki, cong_cu_luu_file, cong_cu_doc_file, cong_cu_gia_crypto]

# =====================================================================
# PHẦN 3: ĐÀO TẠO AGENT
# =====================================================================
agent = create_react_agent(llm, tools=danh_sach_tools)

# =====================================================================
# PHẦN 4: QUẢN LÝ LỊCH SỬ (TRÍ NHỚ DÀI HẠN) VÀ GIAO DIỆN CHAT
# =====================================================================
chi_thi_he_thong = """
Bạn là một trợ lý ảo siêu việt kiêm thư ký cá nhân tên là Agent-007.
Quy tắc:
1. Khi TẠO/LƯU file, dùng 'cong_cu_luu_file'.
2. Khi ĐỌC/XEM nội dung file, dùng 'cong_cu_doc_file'.
3. Khi tìm thông tin kiến thức chung, dùng 'cong_cu_tra_cuu_wiki'.
4. Khi hỏi giá tiền điện tử (Bitcoin, ETH...), BẮT BUỘC dùng 'cong_cu_gia_crypto'.
5. Luôn trả lời lịch sự và trình bày đẹp mắt (dùng Markdown).
"""

FILE_TRI_NHO = "chat_history.json"

def luu_tri_nho(messages):
    try:
        danh_sach_dict = messages_to_dict(messages)
        with open(FILE_TRI_NHO, "w", encoding="utf-8") as f:
            json.dump(danh_sach_dict, f, ensure_ascii=False, indent=2)
    except Exception as e:
        st.error(f"Lỗi khi lưu trí nhớ: {e}")

def tai_tri_nho():
    if os.path.exists(FILE_TRI_NHO):
        try:
            with open(FILE_TRI_NHO, "r", encoding="utf-8") as f:
                danh_sach_dict = json.load(f)
            return messages_from_dict(danh_sach_dict)
        except Exception:
            return None
    return None

with st.sidebar:
    st.header("⚙️ Cài đặt Agent")
    st.markdown("Hệ thống tự động lưu trữ cuộc trò chuyện của bạn vào máy tính.")
    if st.button("🗑️ Xóa sạch trí nhớ", use_container_width=True):
        st.session_state.lich_su_chat = [SystemMessage(content=chi_thi_he_thong)]
        luu_tri_nho(st.session_state.lich_su_chat)
        st.success("Đã tẩy não Agent thành công!")
        st.rerun()

if "lich_su_chat" not in st.session_state:
    tri_nho_cu = tai_tri_nho()
    if tri_nho_cu:
        st.session_state.lich_su_chat = tri_nho_cu
    else:
        st.session_state.lich_su_chat = [SystemMessage(content=chi_thi_he_thong)]

for msg in st.session_state.lich_su_chat:
    if isinstance(msg, HumanMessage):
        with st.chat_message("user"):
            st.markdown(msg.content)
    elif isinstance(msg, AIMessage) and msg.content:
        with st.chat_message("assistant"):
            if isinstance(msg.content, list):
                clean_text = "\n".join([item["text"] for item in msg.content if isinstance(item, dict) and "text" in item])
                st.markdown(clean_text)
            else:
                st.markdown(msg.content)

if cau_hoi := st.chat_input("Nhập lệnh hoặc câu hỏi của bạn vào đây..."):
    with st.chat_message("user"):
        st.markdown(cau_hoi)
        
    st.session_state.lich_su_chat.append(HumanMessage(content=cau_hoi))
    luu_tri_nho(st.session_state.lich_su_chat)
    
    with st.chat_message("assistant"):
        with st.spinner("Agent đang làm việc (tra cứu, đọc/ghi file, tính toán)..."):
            try:
                ket_qua = agent.invoke({"messages": st.session_state.lich_su_chat})
                st.session_state.lich_su_chat = ket_qua["messages"]
                
                luu_tri_nho(st.session_state.lich_su_chat)
                
                final_content = st.session_state.lich_su_chat[-1].content
                if isinstance(final_content, list):
                    clean_text = "\n".join([item["text"] for item in final_content if isinstance(item, dict) and "text" in item])
                    st.markdown(clean_text)
                else:
                    st.markdown(final_content)
                    
            except Exception as e:
                error_msg = str(e)
                if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                    st.error("⏳ **CẢNH BÁO:** Bạn đã chạm giới hạn API. Vui lòng đợi khoảng 1 phút rồi thử lại!")
                    st.session_state.lich_su_chat.pop()
                    luu_tri_nho(st.session_state.lich_su_chat)
                else:
                    st.error(f"❌ **LỖI:** {e}")
                    st.session_state.lich_su_chat.pop()
                    luu_tri_nho(st.session_state.lich_su_chat)