#######################
# Import libraries
import streamlit as st
import pandas as pd
import altair as alt
import plotly.express as px

#######################
# Page configuration
st.set_page_config(
    page_title="US Population Dashboard",
    page_icon="🏂",
    layout="wide",
    initial_sidebar_state="expanded"
)

alt.themes.enable("default")

#######################
# CSS styling (metric 가독성 + 겹침 방지)
st.markdown("""
<style>
[data-testid="block-container"]{
  padding-left:2rem; padding-right:2rem; padding-top:1rem; padding-bottom:0rem;
  /* 겹침 가능성 있는 큰 음수 마진 제거 */
  margin-bottom:0;
}
[data-testid="stVerticalBlock"]{ padding-left:0rem; padding-right:0rem; }

/* Metric tile container */
[data-testid="stMetric"]{
  background-color:#ffffff !important;
  text-align:center;
  padding:16px 10px 18px 10px;
  border:1px solid #e6e6e6;
  border-radius:12px;
  box-shadow:0 1px 3px rgba(0,0,0,0.06);

  /* ✅ 겹침 방지: 컬럼 안에서 100% 너비, 최소/최대 폭 강제, 넘침 숨김 */
  width:100% !important;
  max-width:100% !important;
  min-width:0 !important;
  overflow:hidden;
  box-sizing:border-box;
}

/* Label: 줄바꿈 허용 + 말줄임 제거 + 글자색 강화 */
[data-testid="stMetricLabel"]{
  display:flex; justify-content:center; align-items:center;
  color:#111111 !important;
  font-weight:600;
  line-height:1.15;
}
[data-testid="stMetricLabel"] > div{
  white-space:normal !important;
  overflow:visible !important;
  text-overflow:clip !important;
  word-break:keep-all;
}

/* Value/Delta: 색/크기/줄간격 조정으로 가독성 향상 */
[data-testid="stMetricValue"]{
  color:#111111 !important;
  font-size:34px !important;
  line-height:1.1 !important;
}
[data-testid="stMetricDelta"]{
  color:#111111 !important;
  margin-top:6px;
}

/* Delta icons position */
[data-testid="stMetricDeltaIcon-Up"],
[data-testid="stMetricDeltaIcon-Down"]{
  position:relative; left:38%; transform:translateX(-50%);
}
</style>
""", unsafe_allow_html=True)

#######################
# Load data
df_reshaped = pd.read_csv('titanic (1).csv')  # 분석 데이터 넣기

#######################
# Sidebar
with st.sidebar:
    st.title("Titanic Passenger Dashboard")
    st.caption("필터를 선택하면 전체 시각화가 갱신됩니다.")
    st.markdown("---")

    color_themes = ["blues", "viridis", "plasma", "magma", "inferno"]
    color_theme = st.selectbox("Color theme", color_themes, index=0)
    st.session_state["color_theme"] = color_theme

    st.markdown("### Filters")

    pclass_options = sorted(df_reshaped["Pclass"].dropna().unique().tolist())
    sex_options = sorted(df_reshaped["Sex"].dropna().unique().tolist())
    embarked_options = sorted(df_reshaped["Embarked"].dropna().unique().tolist())

    sel_pclass = st.multiselect("Pclass (등급)", pclass_options, default=pclass_options)
    sel_sex = st.multiselect("Sex (성별)", sex_options, default=sex_options)
    sel_embarked = st.multiselect("Embarked (탑승항)", embarked_options, default=embarked_options)

    age_series = df_reshaped["Age"].dropna()
    fare_series = df_reshaped["Fare"].dropna()
    min_age, max_age = (int(age_series.min()), int(age_series.max())) if not age_series.empty else (0, 80)
    min_fare, max_fare = (float(fare_series.min()), float(fare_series.max())) if not fare_series.empty else (0.0, 520.0)

    age_range = st.slider("Age range", min_value=min_age, max_value=max_age, value=(min_age, max_age))
    include_unknown_age = st.checkbox("Include unknown Age", value=True)

    fare_range = st.slider("Fare range", min_value=float(min_fare), max_value=float(max_fare),
                           value=(float(min_fare), float(max_fare)))
    include_unknown_fare = st.checkbox("Include unknown Fare", value=True)

    st.markdown("---")

    mask = pd.Series(True, index=df_reshaped.index)
    if sel_pclass:   mask &= df_reshaped["Pclass"].isin(sel_pclass)
    if sel_sex:      mask &= df_reshaped["Sex"].isin(sel_sex)
    if sel_embarked: mask &= df_reshaped["Embarked"].isin(sel_embarked)

    age_mask = df_reshaped["Age"].between(age_range[0], age_range[1])
    if include_unknown_age: age_mask |= df_reshaped["Age"].isna()
    mask &= age_mask

    fare_mask = df_reshaped["Fare"].between(fare_range[0], fare_range[1])
    if include_unknown_fare: fare_mask |= df_reshaped["Fare"].isna()
    mask &= fare_mask

    filtered_df = df_reshaped[mask].copy()

    st.metric("Rows after filter", f"{len(filtered_df):,}")
    st.caption("이 결과는 메인 패널과 그래프에 사용됩니다.")

#######################
# Dashboard Main Panel
col = st.columns((1.5, 4.5, 2), gap='medium')

# -------------------- col[0]
with col[0]:
    st.markdown("### 🚢 Summary Statistics")

    total_passengers = len(filtered_df)
    survived_count = int(filtered_df["Survived"].sum())
    died_count = int(total_passengers - survived_count)
    survival_rate = round((survived_count / total_passengers) * 100, 2) if total_passengers > 0 else 0

    c1, c2 = st.columns(2)
    with c1:
        st.metric("Total Passengers", f"{total_passengers:,}")
    with c2:
        st.metric("Survival Rate", f"{survival_rate} %")

    c3, c4 = st.columns(2)
    with c3:
        st.metric("Survived", f"{survived_count:,}", delta=f"{survival_rate}%")
    with c4:
        st.metric("Died", f"{died_count:,}", delta=f"-{round(100 - survival_rate, 2)}%")

    st.markdown("---")

    sex_survival = (
        filtered_df.groupby("Sex")["Survived"].mean().mul(100).round(2).to_dict()
    )
    st.markdown("#### Sex-wise Survival Rate")
    if sex_survival:
        for sex, rate in sex_survival.items():
            st.metric(sex.capitalize(), f"{rate} %")
    else:
        st.caption("⚠️ 선택된 조건에 해당하는 데이터가 없습니다.")

# -------------------- col[1]
with col[1]:
    st.markdown("### 📊 Exploratory Visualizations")

    if filtered_df.empty:
        st.info("선택한 필터에 해당하는 데이터가 없습니다. 사이드바 조건을 변경해 주세요.")
    else:
        tab1, tab2, tab3, tab4 = st.tabs(
            ["Age Distribution", "Fare Distribution", "Survival Heatmap", "Group Summary"]
        )

        # 1) Age Distribution
        with tab1:
            st.caption("생존 여부에 따른 나이 분포 (정규화된 스택 히스토그램)")
            age_df = filtered_df.dropna(subset=["Age"]).copy()
            if age_df.empty:
                st.warning("Age 값이 없는 행만 선택되었습니다.")
            else:
                chart_age = (
                    alt.Chart(age_df)
                    .mark_bar()
                    .encode(
                        x=alt.X("Age:Q", bin=alt.Bin(maxbins=30), title="Age"),
                        y=alt.Y("count():Q", stack="normalize", title="Proportion"),
                        color=alt.Color("Survived:N", title="Survived",
                                        scale=alt.Scale(domain=[0,1], range=["#888888","#1f77b4"])),
                        tooltip=[alt.Tooltip("count():Q", title="Count"),
                                 alt.Tooltip("Survived:N", title="Survived")],
                    ).properties(height=320)
                )
                st.altair_chart(chart_age, use_container_width=True)

        # 2) Fare Distribution
        with tab2:
            st.caption("생존 여부에 따른 운임(Fare) 분포 (로그 스케일 옵션)")
            fare_df = filtered_df.dropna(subset=["Fare"]).copy()
            log_scale = st.checkbox("Use log scale on x (Fare)", value=False, key="fare_log")
            if fare_df.empty:
                st.warning("Fare 값이 없는 행만 선택되었습니다.")
            else:
                x_enc = alt.X("Fare:Q",
                              bin=alt.Bin(maxbins=40),
                              title="Fare (log)" if log_scale else "Fare",
                              scale=alt.Scale(type="log") if log_scale else alt.Undefined)
                chart_fare = (
                    alt.Chart(fare_df)
                    .mark_bar()
                    .encode(
                        x=x_enc,
                        y=alt.Y("count():Q", stack="normalize", title="Proportion"),
                        color=alt.Color("Survived:N", title="Survived",
                                        scale=alt.Scale(domain=[0,1], range=["#888888","#1f77b4"])),
                        tooltip=[alt.Tooltip("count():Q", title="Count"),
                                 alt.Tooltip("Survived:N", title="Survived")],
                    ).properties(height=320)
                )
                st.altair_chart(chart_fare, use_container_width=True)

        # 3) Survival Heatmap (Pclass × Embarked)
        with tab3:
            st.caption("Pclass × Embarked 조합별 평균 생존률(%)")
            heat_df = (
                filtered_df.groupby(["Pclass","Embarked"], dropna=False)["Survived"]
                .mean().mul(100).reset_index()
                .rename(columns={"Survived":"SurvivalRate"})
            )
            heat_df["Embarked"] = heat_df["Embarked"].fillna("Unknown")
            if heat_df.empty:
                st.warning("표시할 조합이 없습니다.")
            else:
                heat = (
                    alt.Chart(heat_df).mark_rect()
                    .encode(
                        x=alt.X("Pclass:N", title="Pclass"),
                        y=alt.Y("Embarked:N", title="Embarked"),
                        color=alt.Color("SurvivalRate:Q", title="Survival Rate (%)",
                                        scale=alt.Scale(scheme=st.session_state.get("color_theme","blues"))),
                        tooltip=[alt.Tooltip("Pclass:N"), alt.Tooltip("Embarked:N"),
                                 alt.Tooltip("SurvivalRate:Q", format=".1f")],
                    ).properties(height=300)
                )
                st.altair_chart(heat, use_container_width=True)

        # 4) Group Summary Table
        with tab4:
            st.caption("성별 × 등급별 요약: 인원, 생존자 수, 생존률(%)")
            summary = (
                filtered_df.groupby(["Sex","Pclass"])
                .agg(count=("PassengerId","count"),
                     survived=("Survived","sum"),
                     survival_rate=("Survived","mean"))
                .reset_index()
            )
            summary["survival_rate"] = (summary["survival_rate"]*100).round(2)
            summary = summary.sort_values(["Sex","Pclass"])
            st.dataframe(summary, use_container_width=True)

# -------------------- col[2]
with col[2]:
    st.markdown("### 🔎 Detailed Insights")

    if filtered_df.empty:
        st.info("선택한 조건에 해당하는 데이터가 없습니다.")
    else:
        tab1, tab2, tab3 = st.tabs(["Top Groups", "Embarked Details", "About"])

        with tab1:
            st.caption("생존률이 높은 그룹과 낮은 그룹을 빠르게 확인합니다.")
            group_df = (
                filtered_df.groupby(["Sex","Pclass"])["Survived"]
                .mean().reset_index().rename(columns={"Survived":"SurvivalRate"})
            )
            group_df["SurvivalRate"] = (group_df["SurvivalRate"]*100).round(2)
            if group_df.empty:
                st.warning("표시할 그룹이 없습니다.")
            else:
                top_groups = group_df.sort_values("SurvivalRate", ascending=False).head(3)
                low_groups = group_df.sort_values("SurvivalRate").head(3)
                st.markdown("#### ⭐ Survival Top 3")
                st.table(top_groups)
                st.markdown("#### ⚠️ Survival Bottom 3")
                st.table(low_groups)

        with tab2:
            st.caption("탑승 항구별 인원 수, 생존자 수, 생존률, 평균 요금(Fare)")
            emb_summary = (
                filtered_df.groupby("Embarked")
                .agg(passengers=("PassengerId","count"),
                     survived=("Survived","sum"),
                     survival_rate=("Survived","mean"),
                     avg_fare=("Fare","mean"))
                .reset_index()
            )
            emb_summary["survival_rate"] = (emb_summary["survival_rate"]*100).round(2)
            emb_summary["avg_fare"] = emb_summary["avg_fare"].round(2)
            emb_summary["Embarked"] = emb_summary["Embarked"].fillna("Unknown")
            if emb_summary.empty:
                st.warning("Embarked 데이터가 없습니다.")
            else:
                st.dataframe(emb_summary, use_container_width=True)

        with tab3:
            st.markdown("#### ℹ️ About this Dashboard")
            st.write("""
            - **Dataset**: Titanic Dataset (Kaggle)
            - **Columns**: `Pclass`, `Sex`, `Age`, `Fare`, `Embarked`, `Survived`
            - **Metrics**: Survival Rate, Top/Bottom Groups, Embarked Details
            """)
