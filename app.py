import streamlit as st
import pandas as pd
from urllib.parse import quote
import io
import requests
import re

# ==========================================
# 🔗 CSV 发布链接
# ==========================================
URL_HERO = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRnMztwr71mxuf6pFYoSLlwBeEcxmNrQp0bfA84u3IJPp5DpBmjUwy4ndnL2Zf8mO6hhL1AzHPAXUx3/pub?gid=1879612607&single=true&output=csv"
URL_TYPE = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRnMztwr71mxuf6pFYoSLlwBeEcxmNrQp0bfA84u3IJPp5DpBmjUwy4ndnL2Zf8mO6hhL1AzHPAXUx3/pub?gid=384260746&single=true&output=csv"
URL_STRATEGY = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRnMztwr71mxuf6pFYoSLlwBeEcxmNrQp0bfA84u3IJPp5DpBmjUwy4ndnL2Zf8mO6hhL1AzHPAXUx3/pub?gid=569984786&single=true&output=csv"

# ==========================================
# 💎 终极视觉优化 + 微信防黑补丁 (CSS)
# ==========================================
st.set_page_config(page_title="AI 全数据护肤系统", layout="wide")

st.markdown("""
    <style>
    /* 强制全局与侧边栏背景为浅色，彻底击败微信深色模式 */
    .stApp, [data-testid="stSidebar"], [data-testid="stSidebar"] > div:first-child { 
        background-color: #F8FAFC !important; 
    }
    
    /* 强制所有常规文字为深灰色，防止看不见 */
    .stApp p, .stApp span, .stApp li, .stApp label, .streamlit-expanderHeader {
        color: #1E293B !important;
    }
    
    /* 保护特殊区块文字颜色 */
    div.stButton > button * { color: white !important; }
    div[data-testid="stInfo"] p, div[data-testid="stWarning"] p { color: inherit !important; }
    .stCaption, .stCaption p { color: #64748B !important; }

    /* 统一标题样式 */
    .custom-title {
        font-size: clamp(1.2rem, 4.5vw, 1.5rem);
        font-weight: 800;
        color: #0F172A !important;
        margin-top: 10px;
        margin-bottom: 15px;
    }
    h1, h2, h3, h4, h5, h6 {
        font-size: clamp(1.1rem, 4vw, 1.3rem) !important;
        color: #0F172A !important;
        font-weight: 700 !important;
    }
    
    /* 显眼的左上角提示横幅 (Banner) */
    .hint-banner {
        background-color: #EFF6FF;
        border-left: 4px solid #3B82F6;
        padding: 12px 16px;
        border-radius: 0 8px 8px 0;
        margin-bottom: 25px;
        box-shadow: 0 2px 4px rgba(59, 130, 246, 0.1);
        display: flex;
        align-items: center;
    }
    .hint-banner span {
        color: #1D4ED8 !important;
        font-weight: 600;
        font-size: 0.95rem;
    }
    
    /* 卡片式容器设计 */
    [data-testid="stVerticalBlock"] > div > div > div[style*="border"] {
        background-color: white !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 12px !important;
        padding: 20px !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05) !important;
    }
    
    /* 侧边栏内的折叠面板强制白底黑字 */
    [data-testid="stSidebar"] [data-testid="stExpander"] {
        background-color: #FFFFFF !important;
        border-radius: 8px !important;
        border: 1px solid #E2E8F0 !important;
    }
    
    /* 按钮样式优化 */
    div.stButton > button {
        background: linear-gradient(90deg, #3B82F6 0%, #2563EB 100%);
        color: white;
        border-radius: 8px;
        font-weight: 600;
        padding: 12px 0;
    }
    
    /* 成分卡片 */
    .ing-card {
        background: #F1F5F9;
        padding: 12px;
        border-radius: 8px;
        text-align: center;
        margin-bottom: 10px;
        min-height: 80px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    .ing-card b { color: #0F172A !important; font-size: 0.95rem; }
    .ing-card span { color: #64748B !important; font-size: 0.8rem; margin-top: 4px; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 🛠️ 核心逻辑
# ==========================================
def find_col(df, keywords):
    for col in df.columns:
        if any(key in col for key in keywords):
            return col
    return None

def convert_google_drive_url(url):
    if 'drive.google.com' in str(url) and '/file/d/' in str(url):
        try:
            file_id = url.split('/file/d/')[1].split('/')[0]
            return f"https://drive.google.com/uc?export=view&id={file_id}"
        except: return url
    return url

def safe_read_csv(url):
    try:
        safe_url = quote(url, safe=':/?&=')
        response = requests.get(safe_url)
        response.encoding = 'utf-8'
        return pd.read_csv(io.StringIO(response.text)) if response.status_code == 200 else pd.DataFrame()
    except: return pd.DataFrame()

@st.cache_data(ttl=60)
def load_all_data():
    df_hero, df_type, df_strategy = safe_read_csv(URL_HERO), safe_read_csv(URL_TYPE), safe_read_csv(URL_STRATEGY)
    for df in [df_hero, df_type, df_strategy]:
        if not df.empty:
            df.columns = df.columns.str.strip()
            for col in df.select_dtypes(include=['object']):
                df[col] = df[col].astype(str).str.strip().replace('nan', pd.NA).str.replace('，', ',').str.replace('、', ',')
    return df_hero, df_type, df_strategy

def main():
    # 顶部标题去掉了丑陋的括号
    st.markdown('<div class="custom-title">🧪 AI 专业护肤成分推荐系统</div>', unsafe_allow_html=True)
    
    # 全新的左上角高颜值提示 Banner
    st.markdown("""
        <div class="hint-banner">
            <span>👈 请先点击左上角【 > 】展开菜单，进行肤质鉴定</span>
        </div>
    """, unsafe_allow_html=True)
    
    df_hero, df_profile, df_strategy = load_all_data()
    if df_profile.empty:
        st.error("正在同步数据，请稍后...")
        return

    col_feel = find_col(df_profile, ['感受', '感', 'Feel'])
    col_visual = find_col(df_profile, ['特征', '特徵', 'Visual'])
    col_title = find_col(df_profile, ['标题', '標題', 'Title'])
    col_strat = find_col(df_profile, ['策略', 'Strategy'])

    if 'step' not in st.session_state: st.session_state.step = 1
    if 'current_skin' not in st.session_state: st.session_state.current_skin = None

    with st.sidebar:
        st.markdown('<div class="custom-title" style="margin-top:0;">👤 肤质鉴定</div>', unsafe_allow_html=True)
        all_options = df_profile.iloc[:, 0].unique().tolist()
        selected_skin = st.selectbox("🎯 选定您的肌肤类型", all_options, label_visibility="collapsed")
        
        if selected_skin != st.session_state.current_skin:
            st.session_state.current_skin, st.session_state.step = selected_skin, 1
            
        st.markdown("---")
        st.markdown('<div class="custom-title" style="font-size:1.1rem;">📖 肤质对比指南</div>', unsafe_allow_html=True)
        for _, row in df_profile.iterrows():
            name = row.iloc[0]
            with st.expander(f"{row.get('Icon', '✨')} {name}", expanded=(name == selected_skin)):
                st.markdown(f"**感受**：{str(row.get(col_feel, '暂无'))}")
                st.markdown(f"**特征**：{str(row.get(col_visual, '暂无'))}")

    profile_row = df_profile[df_profile.iloc[:, 0] == selected_skin]
    if not profile_row.empty:
        user_profile = profile_row.iloc[0]
        st.markdown(f'### {user_profile.get("Icon", "✨")} 已确认为：{selected_skin}')
        st.caption(f"定义参考：{user_profile.get(col_title, '')}")
        
        c1, c2 = st.columns(2)
        with c1:
            with st.container(border=True):
                st.markdown("**💬 核心感受**")
                st.info(str(user_profile.get(col_feel, '暂无资料')).replace(',', '  \n'))
        with c2:
            with st.container(border=True):
                st.markdown("**👁️ 视觉特写**")
                st.warning(str(user_profile.get(col_visual, '暂无资料')).replace(',', '  \n'))

    if st.session_state.step == 1:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("✨ 没问题，这就是我！生成方案", use_container_width=True):
            st.session_state.step = 2
            st.rerun()
            
    if st.session_state.step == 1: return

    st.markdown("---")
    st.markdown(f"### 🛡️ {selected_skin} 建议方案")

    if col_strat and not profile_row.empty:
        current_strategies = [s.strip() for s in str(profile_row.iloc[0][col_strat]).split(',') if s.strip()]
        col_cat = find_col(df_hero, ['分类', '分類', 'Category'])
        col_score = find_col(df_hero, ['分数', '分數', 'Score'])
        col_name = find_col(df_hero, ['中文', 'Name'])
        col_inci = find_col(df_hero, ['INCI'])
        col_desc = find_col(df_hero, ['功效', '描述', 'Desc'])

        for strategy in current_strategies:
            with st.container(border=True):
                st.markdown(f"#### 🎯 核心策略：{strategy}")
                strat_info = df_strategy[df_strategy.iloc[:, 0] == strategy]
                
                if not strat_info.empty:
                    img_urls = [convert_google_drive_url(strat_info.iloc[0, i]) for i in [2, 3, 4] 
                                if len(strat_info.columns) > i and pd.notna(strat_info.iloc[0, i]) and str(strat_info.iloc[0, i]).startswith('http')]
                    if img_urls:
                        cols = st.columns(len(img_urls))
                        for idx, url in enumerate(img_urls): cols[idx].image(url, use_container_width=True)
                    with st.expander("💡 想知道更多.....", expanded=False):
                        st.markdown(str(strat_info.iloc[0, 1]).replace('\n', '  \n'))

                st.markdown("**✨ 推荐成分**")
                mask = df_hero[col_cat].str.contains(strategy, na=False)
                df_hero[col_score] = pd.to_numeric(df_hero[col_score], errors='coerce').fillna(0)
                top_ings = df_hero[mask].sort_values(by=col_score, ascending=False).head(5)

                if not top_ings.empty:
                    n_ings = len(top_ings)
                    ing_cols = st.columns(n_ings)
                    for i, (_, row) in enumerate(top_ings.iterrows()):
                        with ing_cols[i]:
                            st.markdown(f"""
                                <div class="ing-card">
                                    <b>{row[col_name]}</b>
                                    <span>{'★'*int(row[col_score])}</span>
                                </div>
                            """, unsafe_allow_html=True)
                            with st.expander("解析"):
                                st.caption(row[col_inci])
                                st.write(row[col_desc])

                if not strat_info.empty:
                    video_data = []
                    for i in [5, 6, 7]:
                        if len(strat_info.columns) > i:
                            val = str(strat_info.iloc[0, i]).replace('｜', '|').strip()
                            if val.startswith('http') or '|' in val:
                                t, u = val.split('|', 1) if '|' in val else (None, val)
                                if u.strip().startswith('http'): video_data.append({"title": t, "url": u.strip()})
                    if video_data:
                        st.markdown("**🎬 视频指导**")
                        h = """<div style="display: flex; overflow-x: auto; gap: 12px; padding-bottom: 10px; width: 100%;">"""
                        for idx, item in enumerate(video_data):
                            ttl = item["title"] if item["title"] else f"视频 {idx+1}"
                            if 'bilibili.com' in item["url"] or 'b23.tv' in item["url"]:
                                bv = re.search(r'(BV[a-zA-Z0-9]+)', item["url"])
                                bvid = bv.group(1) if bv else ""
                                h += f"""<div style="flex: 0 0 260px;"><div style="font-size: 13px; font-weight: 600; margin-bottom: 5px; color:#1E293B;">{ttl}</div><iframe src="https://player.bilibili.com/player.html?bvid={bvid}&page=1&high_quality=1&danmaku=0" scrolling="no" border="0" frameborder="no" framespacing="0" allowfullscreen="true" style="width: 100%; height: 150px; border-radius: 8px;"></iframe></div>"""
                            else:
                                h += f"""<div style="flex: 0 0 260px;"><div style="font-size: 13px; font-weight: 600; margin-bottom: 5px; color:#1E293B;">{ttl}</div><video controls style="width: 100%; height: 150px; border-radius: 8px; background: #000;"><source src="{item["url"]}" type="video/mp4"></video></div>"""
                        st.markdown(re.sub(r'\s+', ' ', h + "</div>"), unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
