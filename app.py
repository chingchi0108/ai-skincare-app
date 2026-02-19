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
# 📱 极简 CSS：仅保留字体自适应与滑动容器，去除所有颜色干预
# ==========================================
st.set_page_config(page_title="AI 全数据护肤系统", layout="wide")

st.markdown("""
    <style>
    /* 仅根据手机屏幕大小微调标题，完全保留 Streamlit 原生颜色体系 */
    h1 { font-size: clamp(1.2rem, 5vw, 2.2rem) !important; }
    h2 { font-size: clamp(1.1rem, 4vw, 1.8rem) !important; }
    h3 { font-size: clamp(1.0rem, 3.5vw, 1.5rem) !important; }
    h4 { font-size: clamp(0.9rem, 3vw, 1.2rem) !important; }
    h5 { font-size: clamp(0.85rem, 2.8vw, 1.1rem) !important; }
    
    [data-testid="stSidebar"] { width: 300px; }
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
    # 💡 使用独立 CSS 样式单独放大了这个主标题
    st.markdown('<div style="font-size: clamp(1.5rem, 6vw, 2.2rem); font-weight: bold; margin-bottom: 0.8rem;">🧪 AI 全数据护肤系统</div>', unsafe_allow_html=True)
    
    # 使用原生的 st.info 来展示提示，干净且兼容所有主题
    st.info("👈 请先点击左上角【 > 】展开菜单，进行肤质鉴定")
    
    df_hero, df_profile, df_strategy = load_all_data()
    if df_profile.empty:
        st.error("数据加载中，请稍后...")
        return

    col_feel = find_col(df_profile, ['感受', '感', 'Feel'])
    col_visual = find_col(df_profile, ['特征', '特徵', 'Visual'])
    col_title = find_col(df_profile, ['标题', '標題', 'Title'])
    col_strat = find_col(df_profile, ['策略', 'Strategy'])

    if 'step' not in st.session_state: st.session_state.step = 1
    if 'current_skin' not in st.session_state: st.session_state.current_skin = None

    # --- 1. 侧边栏 ---
    all_options = df_profile.iloc[:, 0].unique().tolist()
    with st.sidebar:
        st.header("👤 肤质鉴定")
        selected_skin = st.selectbox("选定您的肌肤类型", all_options, label_visibility="collapsed")

        if selected_skin != st.session_state.current_skin:
            st.session_state.current_skin, st.session_state.step = selected_skin, 1

        st.markdown("---")
        st.markdown("#### 📖 肤质对比指南")
        for _, row in df_profile.iterrows():
            name = row.iloc[0]
            icon = row.get('Icon', '✨')
            with st.expander(f"{icon} {name}", expanded=(name == selected_skin)):
                st.markdown("**💬 感受：**")
                st.caption(str(row.get(col_feel, '暂无')).replace(',', '、\n'))
                st.markdown("**👁️ 特征：**")
                st.caption(str(row.get(col_visual, '暂无')).replace(',', '、\n'))

    # --- 2. 核心鉴定结果 ---
    profile_row = df_profile[df_profile.iloc[:, 0] == selected_skin]
    if not profile_row.empty:
        user_profile = profile_row.iloc[0]
        icon = user_profile.get('Icon', '✨')
        title = user_profile.get(col_title, '')
        
        st.markdown(f"### {icon} 已确认为：{selected_skin}")
        st.caption(f"定义参考：{title}")
        
        col1, col2 = st.columns(2)
        with col1:
            with st.container(border=True):
                st.markdown("#### 💬 核心感受")
                st.info(str(user_profile.get(col_feel, '暂无资料')).replace(',', '  \n'))
        with col2:
            with st.container(border=True):
                st.markdown("#### 👁️ 视觉特写")
                st.warning(str(user_profile.get(col_visual, '暂无资料')).replace(',', '  \n'))

    # --- 确认按钮 ---
    if st.session_state.step == 1:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("✨ 没问题，这就是我！生成方案", use_container_width=True, type="primary"):
            st.session_state.step = 2
            st.rerun()

    if st.session_state.step == 1: return

    # --- 3. 建议方案 ---
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

            # --- 成分展示回归第一版的 2 列布局，并确保提取 5 个 ---
            st.markdown("##### ✨ 推荐成分")
            mask = df_hero[col_cat].str.contains(strategy, na=False)
            df_hero[col_score] = pd.to_numeric(df_hero[col_score], errors='coerce').fillna(0)
            top_ings = df_hero[mask].sort_values(by=col_score, ascending=False).head(5)

            if not top_ings.empty:
                ing_cols = st.columns(2)
                for i, (_, row) in enumerate(top_ings.iterrows()):
                    with ing_cols[i % 2]:
                        with st.expander(f"🏆 {row[col_name]}"):
                            st.caption(f"INCI: {row[col_inci]}")
                            score = int(row[col_score])
                            st.write(f"推荐指数: {'★' * score}")
                            st.progress(score * 20)
                            st.markdown(f"**功效：**\n{row[col_desc]}")

            # 影音指导保留原生格式，去除颜色干预
            if not strat_info.empty:
                video_data = []
                for i in [5, 6, 7]:
                    if len(strat_info.columns) > i:
                        val = str(strat_info.iloc[0, i]).replace('｜', '|').strip()
                        if val.startswith('http') or '|' in val:
                            t, u = val.split('|', 1) if '|' in val else (None, val)
                            if u.strip().startswith('http'): video_data.append({"title": t, "url": u.strip()})
                
                if video_data:
                    st.markdown("##### 🎬 视频指导")
                    h = """<div style="display: flex; overflow-x: auto; gap: 12px; padding-bottom: 10px; width: 100%;">"""
                    for idx, item in enumerate(video_data):
                        ttl = item["title"] if item["title"] else f"视频 {idx+1}"
                        if 'bilibili.com' in item["url"] or 'b23.tv' in item["url"]:
                            bv = re.search(r'(BV[a-zA-Z0-9]+)', item["url"])
                            bvid = bv.group(1) if bv else ""
                            h += f"""<div style="flex: 0 0 260px;"><div style="font-size: 13px; font-weight: bold; margin-bottom: 5px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{ttl}</div><iframe src="https://player.bilibili.com/player.html?bvid={bvid}&page=1&high_quality=1&danmaku=0" scrolling="no" border="0" frameborder="no" framespacing="0" allowfullscreen="true" style="width: 100%; height: 160px; border-radius: 8px;"></iframe><a href="{item["url"]}" target="_blank" style="font-size: 12px; text-decoration: none;">🔗 B站观看</a></div>"""
                        else:
                            h += f"""<div style="flex: 0 0 260px;"><div style="font-size: 13px; font-weight: bold; margin-bottom: 5px;">{ttl}</div><video controls style="width: 100%; height: 160px; border-radius: 8px; background: #000;"><source src="{item["url"]}" type="video/mp4"></video></div>"""
                    st.markdown(re.sub(r'\s+', ' ', h + "</div>"), unsafe_allow_html=True)
            st.markdown("---")

if __name__ == "__main__":
    main()
