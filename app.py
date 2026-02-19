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

st.set_page_config(page_title="AI 全数据护肤系统", layout="wide")

def convert_google_drive_url(url):
    """将 Google Drive 分享网址转换为直连网址"""
    if 'drive.google.com' in str(url) and '/file/d/' in str(url):
        try:
            file_id = url.split('/file/d/')[1].split('/')[0]
            return f"https://drive.google.com/uc?export=view&id={file_id}"
        except IndexError:
            return url
    return url

def safe_read_csv(url):
    try:
        safe_url = quote(url, safe=':/?&=')
        response = requests.get(safe_url)
        response.encoding = 'utf-8'
        if response.status_code == 200:
            return pd.read_csv(io.StringIO(response.text))
        return pd.DataFrame()
    except:
        return pd.DataFrame()

@st.cache_data(ttl=60)
def load_all_data():
    df_hero = safe_read_csv(URL_HERO)
    df_type = safe_read_csv(URL_TYPE)
    df_strategy = safe_read_csv(URL_STRATEGY)

    for df in [df_hero, df_type, df_strategy]:
        if not df.empty:
            df.columns = df.columns.str.strip()
            for col in df.select_dtypes(include=['object']):
                df[col] = df[col].astype(str).str.strip().replace('nan', pd.NA).str.replace('，', ',').str.replace('、', ',')
    
    return df_hero, df_type, df_strategy

def main():
    st.markdown("# 🧪 AI 专业护肤成分推荐系统")
    df_hero, df_profile, df_strategy = load_all_data()

    if df_profile.empty:
        st.error("无法载入肤质资料，请检查 Google Sheets 链接。")
        return

    # ==========================================
    # 🧠 Session State 状态管理 (控制步骤显示)
    # ==========================================
    if 'step' not in st.session_state:
        st.session_state.step = 1
    if 'current_skin' not in st.session_state:
        st.session_state.current_skin = None

    # --- 1. 侧边栏：直觉式肤质选择与对照表 ---
    all_options = df_profile.iloc[:, 0].unique().tolist()
    
    with st.sidebar:
        st.header("👤 第一步：肤质鉴定")
        st.write("请对照下方的特征指南，选择最符合您的肌肤类型：")
        
        # 核心选择器
        selected_skin = st.selectbox("🎯 点此选择肌肤类型", all_options)

        # 检查是否切换了肤质，如果切换了，将步骤重置回 1 (隐藏第二阶段)
        if selected_skin != st.session_state.current_skin:
            st.session_state.current_skin = selected_skin
            st.session_state.step = 1

        st.markdown("---")
        st.markdown("### 📖 肤质特征指南")
        st.caption("点开下方选单，查看各肤质的详细特征：")
        
        for _, row in df_profile.iterrows():
            skin_name = row.iloc[0]
            icon = row.get('Icon') if pd.notna(row.get('Icon')) else '✨'
            is_expanded = (skin_name == selected_skin)
            
            with st.expander(f"{icon} {skin_name}", expanded=is_expanded):
                # 兼容繁简体的栏位抓取
                feel_col = '自我感受' if '自我感受' in row else '自我感受'
                visual_col = '視覺特徵' if '視覺特徵' in row else ('视觉特征' if '视觉特征' in row else None)
                
                feel_text = str(row.get(feel_col, '暂无资料')).replace(',', '、\n')
                visual_text = str(row.get(visual_col, '暂无资料')).replace(',', '、\n')
                
                st.markdown("**💬 感受：**")
                st.caption(feel_text)
                st.markdown("**👁️ 特征：**")
                st.caption(visual_text)

    # --- 2. 阶段一：选定肤质结果展示 ---
    profile_row = df_profile[df_profile.iloc[:, 0] == selected_skin]
    if not profile_row.empty:
        user_profile = profile_row.iloc[0]
        icon = user_profile.get('Icon') if pd.notna(user_profile.get('Icon')) else '✨'
        title = user_profile.get('標題', user_profile.get('标题', ''))
        
        feel_col = '自我感受'
        visual_col = '視覺特徵' if '視覺特徵' in user_profile else '视觉特征'
        
        feel = user_profile.get(feel_col) if pd.notna(user_profile.get(feel_col)) else '暂无资料'
        visual = user_profile.get(visual_col) if pd.notna(user_profile.get(visual_col)) else '暂无资料'

        st.markdown(f"## {icon} 您选择了：**{selected_skin}** — **「{title}」**")
        col1, col2 = st.columns(2)
        with col1:
            with st.container(border=True):
                st.markdown("#### 💬 确认您的自我感受")
                st.info(str(feel).replace(',', ' \n\n'))
        with col2:
            with st.container(border=True):
                st.markdown("#### 👁️ 确认您的视觉特征")
                st.warning(str(visual).replace(',', ' \n\n'))

    # ==========================================
    # 🚧 阶段切换卡榫：解锁后续内容的按钮
    # ==========================================
    if st.session_state.step == 1:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("✨ 没错，这就是我！点击生成专属保养方案 ✨", use_container_width=True, type="primary"):
            st.session_state.step = 2
            st.rerun()  # 触发画面重整，推进到第二步

    # 如果步骤还在 1，就直接 return 中断执行，不显示下方内容
    if st.session_state.step == 1:
        return

    st.markdown("---")

    # --- 3. 阶段二：应对策略及成分推荐 (解锁后显示) ---
    st.subheader(f"🛡️ {selected_skin}：专属应对策略与成分")

    current_strategies = []
    if not profile_row.empty:
        strategy_col = next((c for c in df_profile.columns if '策略' in c or '策略' in c), None)
        if strategy_col and pd.notna(profile_row.iloc[0][strategy_col]):
            raw_strategy = profile_row.iloc[0][strategy_col]
            current_strategies = [s.strip() for s in str(raw_strategy).split(',') if s.strip()]

    if not df_hero.empty and current_strategies:
        col_cat = next((c for c in df_hero.columns if '分類' in c or '分类' in c), df_hero.columns[1] if len(df_hero.columns) > 1 else None)
        col_score = next((c for c in df_hero.columns if '分數' in c or '分数' in c or 'Score' in c), df_hero.columns[4] if len(df_hero.columns) > 4 else None)
        col_name = next((c for c in df_hero.columns if '中文' in c), df_hero.columns[0])
        col_inci = next((c for c in df_hero.columns if 'INCI' in c), df_hero.columns[2] if len(df_hero.columns) > 2 else None)
        col_desc = next((c for c in df_hero.columns if '功效' in c or '描述' in c), df_hero.columns[3] if len(df_hero.columns) > 3 else None)

        for strategy in current_strategies:
            st.markdown(f"### 🎯 策略目标：{strategy}")
            
            strat_info = pd.DataFrame()
            if not df_strategy.empty:
                strat_info = df_strategy[df_strategy.iloc[:, 0] == strategy]
                if not strat_info.empty:
                    info_text_raw = strat_info.iloc[0, 1] if len(strat_info.columns) > 1 else ""
                    info_text = str(info_text_raw).replace('\n', '  \n') if pd.notna(info_text_raw) else "暂无详细说明"
                    
                    # --- 图片处理 ---
                    image_urls = []
                    for col_idx in [2, 3, 4]: # C, D, E 栏
                        if len(strat_info.columns) > col_idx:
                            raw_url = strat_info.iloc[0, col_idx]
                            if pd.notna(raw_url) and str(raw_url).strip().startswith('http'):
                                img_url = convert_google_drive_url(raw_url)
                                image_urls.append(img_url)

                    if image_urls:
                        cols = st.columns(len(image_urls))
                        for idx, img_url in enumerate(image_urls):
                            with cols[idx]:
                                st.image(img_url, use_container_width=True)
                    
                    with st.expander("💡 展开了解此策略详情", expanded=False):
                        st.markdown(info_text)

            # 👉 1. 显示英雄成分推荐
            mask = df_hero[col_cat].str.contains(strategy, na=False)
            df_hero[col_score] = pd.to_numeric(df_hero[col_score], errors='coerce').fillna(0)
            top_ingredients = df_hero[mask].sort_values(by=col_score, ascending=False).head(5)

            st.markdown("#### ✨ 推荐成分")
            if not top_ingredients.empty:
                cols = st.columns(2)
                for idx, (_, row) in enumerate(top_ingredients.iterrows()):
                    with cols[idx % 2]:
                        ingredient_name = row[col_name] if pd.notna(row[col_name]) else "未知成分"
                        with st.expander(f"🏆 **{ingredient_name}**"):
                            inci = row[col_inci] if col_inci and pd.notna(row[col_inci]) else "N/A"
                            desc = row[col_desc] if col_desc and pd.notna(row[col_desc]) else "暂无描述"
                            
                            st.caption(f"INCI: {inci}")
                            score = int(row[col_score])
                            st.write(f"推荐指数：{'★' * score}")
                            st.progress(score * 20)
                            st.markdown(f"**功效**：\n{desc}")
            else:
                 st.caption(f"目前没有针对「{strategy}」的特定成分推荐。")

            # 👉 2. 影片处理
            if not strat_info.empty:
                video_data = []
                for col_idx in [5, 6, 7]: # F, G, H 栏
                    if len(strat_info.columns) > col_idx:
                        raw_cell_value = strat_info.iloc[0, col_idx]
                        if pd.notna(raw_cell_value) and str(raw_cell_value).strip():
                            cell_str = str(raw_cell_value).strip()
                            cell_str = cell_str.replace('｜', '|') 
                            
                            if '|' in cell_str:
                                parts = cell_str.split('|', 1)
                                video_title = parts[0].strip()
                                vid_url = parts[1].strip()
                            else:
                                video_title = None 
                                vid_url = cell_str
                            
                            if vid_url.startswith('http'):
                                video_data.append({"title": video_title, "url": vid_url})
                
                if video_data:
                    st.markdown("#### 🎬 相关影音")
                    
                    html_content = """<div style="display: flex; overflow-x: auto; gap: 16px; padding-bottom: 12px; width: 100%; font-family: sans-serif;">"""
                    
                    for idx, item in enumerate(video_data):
                        display_title = item["title"] if item["title"] else f"🎬 推荐影片 {idx + 1}"
                        vid_url = item["url"]
                        
                        if 'bilibili.com' in vid_url or 'b23.tv' in vid_url:
                            match = re.search(r'(BV[a-zA-Z0-9]+)', vid_url)
                            if match:
                                bvid = match.group(1)
                                html_content += f"""
                                <div style="flex: 0 0 320px; display: flex; flex-direction: column;">
                                    <div style="font-size: 15px; font-weight: bold; margin-bottom: 8px; color: #555; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" title="{display_title}">{display_title}</div>
                                    <iframe src="https://player.bilibili.com/player.html?bvid={bvid}&page=1&high_quality=1&danmaku=0&autoplay=0" 
                                            scrolling="no" border="0" frameborder="no" framespacing="0" 
                                            allowfullscreen="true" webkitallowfullscreen="true" mozallowfullscreen="true"
                                            style="width: 100%; height: 200px; border-radius: 8px; background-color: #000;">
                                    </iframe>
                                    <a href="{vid_url}" target="_blank" style="font-size: 13px; color: #0078D7; text-decoration: none; margin-top: 6px; text-align: center;">
                                        🔗 若无法播放，点击前往 Bilibili 观看
                                    </a>
                                </div>
                                """
                        else:
                            html_content += f"""
                            <div style="flex: 0 0 320px; display: flex; flex-direction: column;">
                                <div style="font-size: 15px; font-weight: bold; margin-bottom: 8px; color: #555; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" title="{display_title}">{display_title}</div>
                                <video controls preload="metadata" style="width: 100%; height: 200px; border-radius: 8px; background-color: #000; object-fit: cover;">
                                    <source src="{vid_url}" type="video/mp4">
                                    您的浏览器不支持影片播放。
                                </video>
                                <a href="{vid_url}" target="_blank" style="font-size: 13px; color: #0078D7; text-decoration: none; margin-top: 6px; text-align: center;">
                                    🔗 点击开启影片链接
                                </a>
                            </div>
                            """
                            
                    html_content += """</div>"""
                    
                    clean_html = re.sub(r'\s+', ' ', html_content).strip()
                    st.markdown(clean_html, unsafe_allow_html=True)

            st.markdown("---")

if __name__ == "__main__":
    main()
