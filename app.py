import streamlit as st
import pandas as pd
from urllib.parse import quote
import io
import requests
import re

# ==========================================
# 🔗 1. CSV 发布链接 (请在此处贴上您的链接)
# ==========================================
URL_HERO = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRnMztwr71mxuf6pFYoSLlwBeEcxmNrQp0bfA84u3IJPp5DpBmjUwy4ndnL2Zf8mO6hhL1AzHPAXUx3/pub?gid=1879612607&single=true&output=csv"
URL_TYPE = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRnMztwr71mxuf6pFYoSLlwBeEcxmNrQp0bfA84u3IJPp5DpBmjUwy4ndnL2Zf8mO6hhL1AzHPAXUx3/pub?gid=384260746&single=true&output=csv"
URL_STRATEGY = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRnMztwr71mxuf6pFYoSLlwBeEcxmNrQp0bfA84u3IJPp5DpBmjUwy4ndnL2Zf8mO6hhL1AzHPAXUx3/pub?gid=569984786&single=true&output=csv"

# 👇 【新增】請在這裡貼上你剛剛發布的 AI_Weekly_Picks 分頁的 CSV 連結
URL_AI_PICKS = "請在這裡貼上你的_AI_Weekly_Picks_CSV_連結" 

# ==========================================
# 📱 2. 极简 CSS
# ==========================================
st.set_page_config(page_title="AI 全数据护肤系统", layout="wide")

st.markdown("""
    <style>
    h1 { font-size: clamp(1.2rem, 5vw, 2.2rem) !important; }
    h2 { font-size: clamp(1.1rem, 4vw, 1.8rem) !important; }
    h3 { font-size: clamp(1.0rem, 3.5vw, 1.5rem) !important; }
    h4 { font-size: clamp(0.9rem, 3vw, 1.2rem) !important; }
    h5 { font-size: clamp(0.85rem, 2.8vw, 1.1rem) !important; }
    
    [data-testid="stSidebar"] { width: 300px; }
    
    /* 优化电商与小红书按钮链接样式 */
    .shop-link {
        display: inline-block;
        padding: 6px 14px;
        margin-top: 8px;
        margin-right: 8px;
        margin-bottom: 8px;
        border-radius: 6px;
        font-size: 0.85rem;
        font-weight: bold;
        text-decoration: none !important;
        color: white !important;
        text-align: center;
    }
    .xhs-link { background-color: #FF2442; } /* 小红书红 */
    .jd-link { background-color: #E1251B; } /* 京东红 */
    .tb-link { background-color: #FF5000; } /* 淘宝橙 */
    .shop-link:hover { opacity: 0.8; transform: translateY(-1px); }
    
    /* 综合推荐卡片底色 */
    .recommend-box {
        background-color: #F8FAFC;
        border-left: 4px solid #3B82F6;
        padding: 15px;
        border-radius: 0 8px 8px 0;
        margin-top: 15px;
        margin-bottom: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 🛠️ 3. 核心逻辑
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
    """安全地讀取 CSV 檔案"""
    if "請在這裡貼上" in url: # 防呆機制，若未填寫網址則回傳空表
        return pd.DataFrame()
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

@st.cache_data(ttl=60)
def load_ai_picks():
    """從 Google Sheet 讀取本週 AI 嚴選清單"""
    df = safe_read_csv(URL_AI_PICKS)
    if not df.empty:
        df.columns = df.columns.str.strip()
    return df

def main():
    st.markdown('<div style="font-size: clamp(1.5rem, 6vw, 2.2rem); font-weight: bold; margin-bottom: 0.8rem;">🧪 AI 全数据护肤系统</div>', unsafe_allow_html=True)
    st.info("👈 请先点击左上角【 > 】展开菜单，进行肤质鉴定")
    
    df_hero, df_profile, df_strategy = load_all_data()
    df_ai_picks = load_ai_picks() # 載入 AI 預先算好的清單
    
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

            # --- 成分展示区块 ---
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
                
                # ==========================================
                # 🛍️ 读取并渲染 AI 严选单品与搜寻按钮
                # ==========================================
                st.markdown("<br>", unsafe_allow_html=True)
                
                st.markdown("""
                    <div style='background-color: #333333; padding: 10px; border-radius: 8px; margin-bottom: 15px;'>
                        <span style='color: #FFD700; font-size: 13px;'>💡 <b>温馨提示：</b> 若在微信内点击下方按钮无反应，请点击右上角「...」选择<b>「在浏览器打开」</b>，即可顺畅唤醒 App 查看。</span>
                    </div>
                """, unsafe_allow_html=True)

                st.markdown(f"""
                <div class="recommend-box">
                    <h5 style="margin-top:0; color:#0F172A;">🤖 本周 AI 严选好物</h5>
                    <p style="font-size:0.9rem; color:#475569; margin-bottom:10px;">
                        针对您的【{strategy}】诉求，AI 机器买手已从全网提取最新配方，为您筛选出以下符合核心成分的口碑爆款。<br>
                        👉 <b>直接点击下方按钮，查看真实测评与全网底价：</b>
                    </p>
                </div>
                """, unsafe_allow_html=True)

                # 从 df_ai_picks 中过滤出属于目前策略的产品
                if not df_ai_picks.empty and 'Strategy' in df_ai_picks.columns:
                    ai_products = df_ai_picks[df_ai_picks['Strategy'] == strategy]
                    
                    if not ai_products.empty:
                        for _, row in ai_products.iterrows():
                            # 讀取對應的欄位，並去除空值
                            prod_name = str(row.get("Product_Name", "")).strip()
                            prod_desc = str(row.get("Product_Desc", "")).strip()
                            
                            # 確保產品名稱不是空的，也不是 nan
                            if prod_name and prod_name.lower() != 'nan':
                                prod_kw = quote(prod_name)
                                # 注意：這裡依然保留了移除 target="_blank" 的設定 (除了京東)，以利微信跳轉
                                st.markdown(f"""
                                    <div style="margin-bottom: 15px; padding: 12px; border: 1px solid #E2E8F0; border-radius: 8px; background-color: #ffffff; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                                        <div style="font-weight: bold; font-size: 1.05rem; color: #1E293B;">🛍️ {prod_name}</div>
                                        <div style="font-size: 0.85rem; color: #64748B; margin-bottom: 10px; margin-top: 4px;">{prod_desc}</div>
                                        <a href="xhsdiscover://search/result?keyword={prod_kw}" class="shop-link xhs-link">📕 搜小红书测评</a>
                                        <a href="https://so.m.jd.com/ware/search.action?keyword={prod_kw}" target="_blank" class="shop-link jd-link">🔴 京东查底价</a>
                                        <a href="taobao://s.taobao.com/search?q={prod_kw}" class="shop-link tb-link">🟠 天猫看爆款</a>
                                    </div>
                                """, unsafe_allow_html=True)
                    else:
                        st.info(f"正在等待 AI 買手為【{strategy}】更新推薦單品...")
                else:
                    st.warning("⚠️ 尚未載入本週 AI 嚴選清單，請確認 URL_AI_PICKS 是否填寫正確。")

            # --- 影音指导 ---
            if not strat_info.empty:
                st.markdown("<br>", unsafe_allow_html=True)
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
